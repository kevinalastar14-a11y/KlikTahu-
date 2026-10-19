#!/usr/bin/env bash
# ============================================================================
#  tools/render_lokal.sh — render KlikTahu di komputer sendiri / sandbox agen.
#
#  PENTING: render video memang TIDAK dijalankan di GitHub Actions (lihat
#  AGEN.md §14). Actions hanya untuk uji ringan (selftest.yml).
#
#  Pakai:
#      tools/render_lokal.sh shorts <slug>            # render penuh
#      tools/render_lokal.sh shorts <slug> prep       # berhenti sebelum render
#      tools/render_lokal.sh long   <slug>            # video panjang 16:9
#
#  Variabel opsional:
#      CHUNKS=12        jumlah potongan (menjaga pemakaian disk frame PNG)
#      JOBS=4           proses paralel per potongan (bawaan: jumlah CPU)
#      KEEP_FRAMES=1    jangan hapus frame setelah tiap potongan di-encode
#
#  Hasil akhir ada di dist/ (mp4 + METADATA.md + content.json; Long juga
#  thumbnail.jpg + SIAP_TEMPEL.md).
# ============================================================================
set -euo pipefail

MODE="${1:-}"
SLUG="${2:-}"
PHASE="${3:-full}"

die() { printf '\n[GAGAL] %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 tidak ditemukan di PATH"; }

usage() {
  sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

[ -n "$MODE" ] && [ -n "$SLUG" ] || usage
case "$MODE" in shorts|long) ;; *) die "mode harus 'shorts' atau 'long'";; esac

cd "$(dirname "$0")/.."          # selalu di akar repo
ROOT="$(pwd)"
need python3

if [ "$MODE" = shorts ]; then DIR="episodes/$SLUG"; else DIR="long/$SLUG"; fi
[ -f "$DIR/config.env" ] || die "tidak ada $DIR/config.env (slug salah?)"

# --- guard: audio mentah memang tidak disimpan di repo ----------------------
shopt -s nullglob
RAW=( "$DIR"/audio_raw/*.wav "$DIR"/audio_raw/*.flac "$DIR"/audio_raw/*.mp3 "$DIR"/audio_raw/*.m4a )
if [ "${#RAW[@]}" -eq 0 ]; then
  die "audio mentah kosong: $DIR/audio_raw/ belum diisi.
       Audio sengaja tidak disimpan di repo — lihat docs/audio-manifest.md
       (arsip: Google Drive 'kliktahu.zip' -> $DIR/audio_raw/)."
fi
printf '[info] %d klip audio mentah untuk %s\n' "${#RAW[@]}" "$DIR"

# --- konfigurasi episode ----------------------------------------------------
# shellcheck disable=SC1090
set -a; source "$DIR/config.env"; set +a
: "${FPS:?config.env belum mengisi FPS}"
: "${OUT_NAME:?config.env belum mengisi OUT_NAME}"

FF="$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')"
CHUNKS="${CHUNKS:-12}"
JOBS="${JOBS:-$( (nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2) )}"
DISK_FRAMES="frames"

echo "=========================================================================="
echo " KlikTahu · $MODE · $SLUG"
echo " FPS=$FPS  SS=${SS:-?}  potongan=$CHUNKS  proses/potongan=$JOBS  fase=$PHASE"
echo "=========================================================================="

# ============================================================ 1) audio + naskah
mkdir -p audio audio_proc build dist
cp "$DIR/content.json" .
cp "${RAW[@]}" audio/
export KT_BUILD=build
# QC akhir memakai ambang waktu yang sama dengan rantai VO v12 dan membandingkan
# audio MP4 dengan master (bukan audio.wav pra-master) -> tanpa ini QC memberi alarm palsu.
export KT_VO_CHAIN="${KT_VO_CHAIN:-v12}"
export KT_AUDIO_SRC="$ROOT/build/audio_master.wav"

MESIN="$(python3 -c 'import json;print(str(json.load(open("content.json")).get("mesin","")).lower())')"
if [ "$MESIN" = v12 ] && [ "${KT_VO_CHAIN:-v12}" = v12 ]; then
  echo "--- vo_manusia.py (v12: VO untuk telinga manusia - tanpa atempo/pemotongan, QC ASR)"
  python3 vo_manusia.py --asr
else
  echo "--- process_audio.py (rapikan VO + QC keutuhan)"
  SPEED="$SPEED" TARGET_WPS="${TARGET_WPS:-1.90}" python3 process_audio.py
fi
echo "--- build_timeline.py"
MAXDUR="${MAXDUR:-180}" python3 build_timeline.py
if python3 -c 'import json,sys; sys.exit(0 if str(json.load(open("content.json")).get("mesin","")).lower()=="v12" else 1)'; then
  echo "--- align_kata.py (v12: BEAT dikunci ke kata)"
  python3 align_kata.py
fi
echo "--- build_audio.py"
SPEED="$SPEED" python3 build_audio.py
echo "--- master_audio.py (loudnorm + SFX)"
python3 master_audio.py

if [ "$MODE" = shorts ]; then
  echo "--- check_layout.py (audit margin)"
  python3 check_layout.py
else
  echo "--- align kata + audio Long + thumbnail"
  python3 long/render_long.py --slug "$SLUG" --align
  mkdir -p build/mix
  python3 long/audio_long.py --slug "$SLUG" --out build/mix/audio_master.wav
  python3 "$DIR/thumbnail.py" --out build/thumbnail.jpg
  AUDIO_MASTER="build/mix/audio_master.wav"
  export KT_AUDIO_SRC="$AUDIO_MASTER"
fi
[ "$MODE" = shorts ] && AUDIO_MASTER="build/audio_master.wav" && export KT_AUDIO_SRC="$AUDIO_MASTER"

if [ "$PHASE" = prep ]; then
  echo
  echo "[prep] selesai — audio, timeline, dan QC tata letak lolos."
  echo "       Jalankan tanpa argumen 'prep' untuk render penuh."
  exit 0
fi

# ============================================================ 2) hitung frame
TOTAL="$(python3 - "$FPS" <<'PY'
import json, sys
fps = float(sys.argv[1])
tl = json.load(open("timeline.json"))
print(int(round(tl["total"] * fps)))
PY
)"
[ "$TOTAL" -gt 0 ] || die "timeline kosong (total frame = 0)"
PER=$(( (TOTAL + CHUNKS - 1) / CHUNKS ))
echo "[info] $TOTAL frame -> $CHUNKS potongan x ~$PER frame"

# ============================================================ 3) render potongan
rm -rf parts "$DISK_FRAMES"; mkdir -p parts
: > list.txt
for i in $(seq 0 $((CHUNKS - 1))); do
  LO=$(( i * PER )); HI=$(( LO + PER ))
  [ "$HI" -gt "$TOTAL" ] && HI="$TOTAL"
  [ "$LO" -ge "$TOTAL" ] && continue
  echo "--- potongan $i: frame $LO..$((HI - 1))"
  rm -rf "$DISK_FRAMES"; mkdir -p "$DISK_FRAMES"
  if [ "$MODE" = shorts ]; then
    python3 render.py --fps "$FPS" --ss "${SS:-1.5}" --sharpen "${SHARPEN:-52}" \
            --jobs "$JOBS" --range "$LO:$HI" --outdir "$DISK_FRAMES"
    "$FF" -y -loglevel error -framerate "$FPS" -start_number "$LO" -i "$DISK_FRAMES/f_%05d.png" \
          -frames:v "$((HI - LO))" -an -c:v libx264 -preset "${PRESET:-slow}" -tune "${TUNE:-animation}" \
          -b:v "${VBITRATE:-6400k}" -maxrate "${MAXRATE:-11000k}" -bufsize "${BUFSIZE:-16000k}" \
          -pix_fmt yuv420p -profile:v high -level 4.2 "parts/part_$i.mp4"
  else
    python3 long/render_long.py --slug "$SLUG" --timeline timeline.json --fps "$FPS" --ss "${SS:-1.25}" \
            --jobs "$JOBS" --range "$LO:$HI" --vb "${VBITRATE:-9000k}" --maxrate "${MAXRATE:-14000k}" \
            --bufsize "${BUFSIZE:-20000k}" --preset "${PRESET:-slow}" --tune "${TUNE:-animation}" \
            --out "parts/part_$i.mp4"
  fi
  [ -s "parts/part_$i.mp4" ] || die "potongan $i tidak menghasilkan mp4"
  echo "file parts/part_$i.mp4" >> list.txt
  [ "${KEEP_FRAMES:-0}" = 1 ] || rm -rf "$DISK_FRAMES"
done
rm -rf "$DISK_FRAMES"

# ============================================================ 4) gabung + mux
echo "--- gabung potongan (tanpa re-encode) + mux audio"
"$FF" -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_master.mp4
"$FF" -y -loglevel error -i video_master.mp4 -i "$AUDIO_MASTER" \
      -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a "${ABITRATE:-256k}" -ar 48000 \
      -movflags +faststart -shortest "dist/${OUT_NAME}.mp4"
ls -la "dist/${OUT_NAME}.mp4"

# ============================================================ 5) QC + serah terima
echo "--- QC akhir (qc_mp4.py)"
python3 qc_mp4.py "dist/${OUT_NAME}.mp4"

cp "$DIR/METADATA.md" dist/ 2>/dev/null || echo "[warn] METADATA.md belum ada di $DIR"
cp "$DIR/content.json" "dist/${OUT_NAME}_content.json"
if [ "$MODE" = long ]; then
  [ -f build/thumbnail.jpg ] && cp build/thumbnail.jpg dist/thumbnail.jpg
  P="pustaka/${OUT_NAME#KlikTahu_}"
  [ -f "$P/SIAP_TEMPEL.md" ] && cp "$P/SIAP_TEMPEL.md" dist/ || true
else
  P="pustaka/${OUT_NAME#KlikTahu_}"
  [ -f "$P/SIAP_TEMPEL.md" ] && cp "$P/SIAP_TEMPEL.md" dist/ || true
fi

echo
echo "=========================================================================="
echo " SELESAI — berkas siap unggah ada di dist/:"
ls -la dist/
echo "=========================================================================="
