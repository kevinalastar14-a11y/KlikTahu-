import os
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class CinematicVideoPipeline:
    def __init__(self, output_file="final_output.mp4"):
        self.output_file = output_file
        self.clips = []
        self.resolution = (1080, 1920)  # YouTube Shorts / TikTok Format
        self.fps = 60 # High framerate for smooth motion
        
    def create_hook(self, text, duration=3.0):
        """
        The Hook: Instantly grabs attention within the first 3 seconds.
        Includes sharp sound effects, fast visual transitions.
        """
        # Placeholder for dynamic text rendering with visual hierarchy
        clip = ColorClip(size=self.resolution, color=(20, 20, 20)).set_duration(duration)
        txt_clip = TextClip(text, fontsize=120, color='white', font='Helvetica-Bold', method='caption', size=(900, None))
        txt_clip = txt_clip.set_position('center').set_duration(duration)
        
        # Apply progressive disclosure & zoom effect (Semantic Animation)
        txt_clip = txt_clip.resize(lambda t: 1 + 0.05 * t)
        
        # Audio syncing (Sound Effects)
        # sfx = AudioFileClip("sfx_whoosh.mp3").set_start(0)
        # clip = clip.set_audio(sfx)
        
        video = CompositeVideoClip([clip, txt_clip])
        self.clips.append(video)
        print(f"[+] Hook created: {text}")

    def create_agitation(self, problem_statement, duration=4.0):
        """
        The Agitation / The Problem: Deepens the hook by presenting the pain point.
        Uses perceptual continuity and depth layering.
        """
        clip = ColorClip(size=self.resolution, color=(30, 10, 10)).set_duration(duration)
        txt_clip = TextClip(problem_statement, fontsize=90, color='red', font='Helvetica-Bold', method='caption', size=(900, None))
        txt_clip = txt_clip.set_position('center').set_duration(duration)
        
        # Cinematic transition (Fade in, then hold, then scale down)
        txt_clip = txt_clip.crossfadein(0.5)
        
        video = CompositeVideoClip([clip, txt_clip])
        self.clips.append(video)
        print(f"[+] Agitation created: {problem_statement}")

    def create_body(self, value_points, duration_per_point=3.0):
        """
        The Body / The Value Delivery: Delivers the core message using progressive disclosure.
        Information architecture and cognitive load management.
        """
        for i, point in enumerate(value_points):
            clip = ColorClip(size=self.resolution, color=(10, 30, 10)).set_duration(duration_per_point)
            txt_clip = TextClip(point, fontsize=80, color='white', font='Helvetica', method='caption', size=(900, None))
            txt_clip = txt_clip.set_position('center').set_duration(duration_per_point)
            
            # Slide in animation (Temporal rhythm)
            txt_clip = txt_clip.set_position(lambda t: ('center', 1920 - (1920/0.5)*t if t < 0.5 else 'center'))
            
            video = CompositeVideoClip([clip, txt_clip])
            self.clips.append(video)
            print(f"[+] Body point created: {point}")

    def create_micro_climax(self, climax_text, duration=3.0):
        """
        The Micro-Climax: The visual payoff, connecting previous elements.
        Visual metaphor, cinematic composition, and dynamic framing.
        """
        clip = ColorClip(size=self.resolution, color=(255, 215, 0)).set_duration(duration) # Gold color
        txt_clip = TextClip(climax_text, fontsize=140, color='black', font='Helvetica-Bold', method='caption', size=(900, None))
        txt_clip = txt_clip.set_position('center').set_duration(duration)
        
        # Rapid acceleration (match cut / impact)
        txt_clip = txt_clip.resize(lambda t: max(1, 2 - t*2))
        
        video = CompositeVideoClip([clip, txt_clip])
        self.clips.append(video)
        print(f"[+] Micro-Climax created: {climax_text}")

    def create_outro_loop(self, outro_text, hook_text, duration=3.0):
        """
        Seamless Outro / The Infinite Loop: Connects visually and temporally back to the Hook.
        """
        clip = ColorClip(size=self.resolution, color=(20, 20, 20)).set_duration(duration)
        
        outro_clip = TextClip(outro_text, fontsize=100, color='white', font='Helvetica', method='caption', size=(900, None))
        outro_clip = outro_clip.set_position('center').set_duration(duration/2)
        
        # Transition back to the hook text to create a seamless loop
        loop_clip = TextClip(hook_text, fontsize=120, color='white', font='Helvetica-Bold', method='caption', size=(900, None))
        loop_clip = loop_clip.set_position('center').set_start(duration/2).set_duration(duration/2)
        
        video = CompositeVideoClip([clip, outro_clip, loop_clip])
        self.clips.append(video)
        print(f"[+] Seamless Outro created: {outro_text} -> {hook_text}")

    def render(self):
        """
        Compiles the clips using cinematic crossfades and seamless morphing.
        """
        print("[!] Rendering the final cinematic video...")
        
        # Apply seamless morphing / transitions between clips
        transitions = [self.clips[0]]
        for i in range(1, len(self.clips)):
            # 0.5s crossfade for seamless temporal transitions
            transition_clip = self.clips[i].crossfadein(0.5)
            transitions.append(transition_clip)
            
        final_video = concatenate_videoclips(transitions, method="compose")
        final_video.write_videofile(self.output_file, fps=self.fps, codec="libx264", audio_codec="aac")
        print(f"[+] Video successfully rendered to {self.output_file}")

if __name__ == "__main__":
    pipeline = CinematicVideoPipeline("KlikTahu_Cinematic.mp4")
    
    hook = "APAKAH ANDA TAHU RAHASIA INI?"
    pipeline.create_hook(hook, duration=3.0)
    
    pipeline.create_agitation("Kebanyakan orang gagal karena satu kesalahan kecil...", duration=4.0)
    
    body_points = [
        "1. Kurangnya pemahaman tentang struktur",
        "2. Tidak ada hierarchy visual",
        "3. Informasi yang terlalu padat (Cognitive Overload)"
    ]
    pipeline.create_body(body_points, duration_per_point=2.5)
    
    pipeline.create_micro_climax("RAHASIANYA ADALAH: PROGRESSIVE DISCLOSURE!", duration=3.0)
    
    pipeline.create_outro_loop("Terapkan ini sekarang, dan...", hook, duration=3.0)
    
    # pipeline.render() # Uncomment to render when ImageMagick is properly configured
