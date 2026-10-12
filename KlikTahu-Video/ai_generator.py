import os
import asyncio
import edge_tts
from openai import OpenAI

# Gunakan model mutakhir GPT-4o
MODEL_NAME = "gpt-4o"

def generate_cinematic_script(topic):
    """
    Menghasilkan script dengan 5 struktur naratif menggunakan GPT-4o.
    1. The Hook
    2. The Agitation
    3. The Body
    4. The Micro-Climax
    5. Seamless Outro
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "DUMMY_KEY"))
    
    prompt = f"""
    Buat script video pendek cinematic tentang topik: {topic}.
    Format harus tepat 5 bagian:
    [HOOK]: Kalimat pendek pemicu penasaran.
    [AGITATION]: Masalah atau rasa sakit yang dialami penonton.
    [BODY]: 3 poin solusi yang diberikan.
    [MICRO_CLIMAX]: Satu kalimat klimaks visual yang kuat.
    [OUTRO]: Kalimat penutup yang seamless loop kembali ke HOOK.
    
    Jangan tambahkan teks lain. Hanya scriptnya saja.
    """
    
    # In production, uncomment the API call
    # response = client.chat.completions.create(
    #     model=MODEL_NAME,
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return response.choices[0].message.content
    
    # Dummy response for demonstration
    return f"""
    [HOOK]: APAKAH ANDA TAHU RAHASIA INI?
    [AGITATION]: Kebanyakan orang gagal karena satu kesalahan kecil yang terus diulang.
    [BODY]: 1. Kurang fokus. 2. Tidak ada hierarki. 3. Overload informasi.
    [MICRO_CLIMAX]: RAHASIANYA ADALAH: PROGRESSIVE DISCLOSURE!
    [OUTRO]: Terapkan ini sekarang, dan...
    """

async def generate_voice_over(text, output_file="vo.mp3"):
    """
    Menggunakan AI Voice mutakhir dengan Edge-TTS untuk menghasilkan Voice-Over.
    Tanpa music background, murni Voice-Over.
    """
    # Menggunakan suara id-ID-ArdiNeural (Indonesian Male) untuk nuansa cinematic/documentary
    communicate = edge_tts.Communicate(text, "id-ID-ArdiNeural", rate="+0%", volume="+0%")
    await communicate.save(output_file)
    print(f"[+] Voice-over saved to {output_file}")

if __name__ == "__main__":
    print("Generating AI Script...")
    script = generate_cinematic_script("Cara Membuat Video Cinematic")
    print(script)
    
    # print("Generating Voice Over...")
    # asyncio.run(generate_voice_over("APAKAH ANDA TAHU RAHASIA INI?", "hook_vo.mp3"))
