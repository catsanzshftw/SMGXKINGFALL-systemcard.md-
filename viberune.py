import pygame
import sys
import random
import math
import numpy
import pygame.sndarray

# --- VIBE ENGINE INITIALIZATION ---
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

# --- CORE SETTINGS (NO FILES) ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60
WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("VIBE ENGINE: DELTARUNE [files=off, audio=on]")
CLOCK = pygame.time.Clock()

# --- PROCEDURAL ASSETS (NO FILES) ---
# Colors are our primary tool for generating vibe.
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'dark_purple': (48, 25, 52),
    'glow_purple': (224, 176, 255),
    'plastic_brown': (87, 65, 47),
    'king_gray': (50, 50, 60),
    'king_chain': (200, 200, 200),
    'spade_black': (20, 20, 20),
    'heart_red': (255, 0, 0),
    'cyber_grid': (20, 30, 80),
    'cyber_neon_pink': (255, 105, 180),
    'cyber_neon_green': (57, 255, 20),
    'spam_basement': (30, 30, 30),
    'spam_yellow': (255, 240, 0),
    'spam_pink': (255, 0, 128),
    'glitch_static': (200, 200, 200),
    'jevil_purple': (128, 0, 255),
    'jevil_yellow': (255, 255, 0),
    'queen_blue': (0, 191, 255),
    'queen_acid': (0, 255, 0),
    'potassium_yellow': (255, 240, 90),
}

# Since we can't load fonts, we use the system default.
MENU_FONT = pygame.font.Font(None, 60)
SCENE_FONT = pygame.font.Font(None, 24)
POPUP_FONT = pygame.font.Font(None, 36)
SPAMTON_FONT = pygame.font.Font(None, 28)

# --- GLOBAL STATE MANAGER ---
scene_elements = {}
music_tracks = {}
sfx_sounds = {}

# --- PROCEDURAL AUDIO ENGINE ---
SAMPLE_RATE = 44100

def make_sound(frequency, duration, attack=0.01, decay=0.1, vol=0.1, wave_func=numpy.sin):
    """Generates a pygame.Sound object with a given frequency and duration."""
    attack_len = int(attack * SAMPLE_RATE)
    decay_len = int(decay * SAMPLE_RATE)
    sustain_len = int(duration * SAMPLE_RATE) - attack_len - decay_len
    
    if sustain_len < 0: # Handle short sounds
        sustain_len = 0
        decay_len = int(duration * SAMPLE_RATE) - attack_len
        if decay_len < 0:
            attack_len = int(duration * SAMPLE_RATE)
            decay_len = 0

    t = numpy.linspace(0, duration, int(duration * SAMPLE_RATE), False)
    wave = wave_func(frequency * t * 2 * numpy.pi)

    # Envelope
    attack_env = numpy.linspace(0, vol, attack_len)
    decay_env = numpy.linspace(vol, 0, decay_len)
    sustain_env = numpy.full(sustain_len, vol)
    
    envelope = numpy.concatenate((attack_env, sustain_env, decay_env))
    
    # Ensure envelope and wave match in length
    if len(envelope) > len(wave):
        envelope = envelope[:len(wave)]
    elif len(wave) > len(envelope):
        wave = wave[:len(envelope)]
        
    sound_wave = wave * envelope
    sound_wave = numpy.repeat(sound_wave.reshape(len(sound_wave), 1), 2, axis=1) # Stereo
    sound = pygame.sndarray.make_sound(numpy.asarray(sound_wave * 32767, dtype=numpy.int16))
    return sound

def make_noise(duration, vol=0.1):
    """Generates white noise."""
    wave = numpy.random.uniform(-1, 1, int(duration * SAMPLE_RATE))
    sound_wave = numpy.repeat(wave.reshape(len(wave), 1), 2, axis=1)
    sound = pygame.sndarray.make_sound(numpy.asarray(sound_wave * vol * 32767, dtype=numpy.int16))
    return sound

# --- FIX: Replaced the original music generation function ---
# The original function did not handle repeated notes correctly.
# This version iterates through notes and builds the sound buffer sequentially, ensuring accuracy.
def generate_music_track(notes, note_duration, vol=0.1, wave_func=numpy.sin):
    """Generates a looping music track from a list of notes (frequencies)."""
    full_track_raw = b""
    # Pre-calculate silence for rests (note frequency = 0)
    silence_buffer = numpy.zeros(int(note_duration * SAMPLE_RATE * 2), dtype=numpy.int16).tobytes()

    for note_freq in notes:
        if note_freq > 0:
            # Generate the sound for the current note and get its raw byte buffer
            sound_buffer = make_sound(note_freq, note_duration, vol=vol, wave_func=wave_func).get_raw()
            full_track_raw += sound_buffer
        else:
            # Append silence for a rest
            full_track_raw += silence_buffer
            
    return pygame.mixer.Sound(buffer=full_track_raw)

def init_audio():
    """Generate all procedural SFX and music on startup."""
    # SFX
    sfx_sounds['menu_move'] = make_sound(440, 0.05, vol=0.05)
    sfx_sounds['menu_select'] = make_sound(880, 0.1, vol=0.08)
    sfx_sounds['glitch'] = make_noise(0.1, vol=0.15)
    sfx_sounds['spade_shoot'] = make_sound(220, 0.2, decay=0.2, vol=0.2, wave_func=lambda t: numpy.sign(numpy.sin(t))) # Square wave
    sfx_sounds['heart_damage'] = make_sound(150, 0.4, decay=0.4, vol=0.3, wave_func=lambda t: numpy.sign(numpy.sin(t)))

    # Music Tracks (Note: 0 is a rest)
    music_tracks["MENU"] = generate_music_track([261, 293, 329, 293], 0.4, vol=0.1)
    music_tracks["CH1: Field"] = generate_music_track([349, 0, 440, 0, 523, 0, 440, 0], 0.3, vol=0.15)
    music_tracks["CH1: King"] = generate_music_track([130, 130, 146, 130, 0, 110, 110, 0], 0.25, vol=0.2, wave_func=lambda t: numpy.sign(numpy.sin(t)))
    music_tracks["CH1: Jevil"] = generate_music_track([392, 370, 349, 330, 311, 293, 277, 261], 0.08, vol=0.15)
    music_tracks["CH2: Cyber City"] = generate_music_track([523, 0, 523, 0, 523, 659, 0, 440], 0.18, vol=0.15, wave_func=lambda t: (t % 1) - 0.5) # Saw wave
    music_tracks["CH2: Queen"] = generate_music_track([659, 0, 659, 0, 622, 0, 659, 0], 0.2, vol=0.2, wave_func=lambda t: numpy.sign(numpy.sin(t)))
    music_tracks["CH2: Spamton"] = generate_music_track([880, 440, 990, 330, 1100, 220, 1200, 110], 0.1, vol=0.2)
    

# --- HELPER & DRAWING FUNCTIONS ---

def draw_text(text, font, color, surface, x, y, center=True):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_heart(x, y, size):
    p1 = (x, y + size)
    p2 = (x - size, y - size * 0.5)
    p3 = (x - size * 0.5, y - size)
    p4 = (x, y - size * 0.5)
    p5 = (x + size * 0.5, y - size)
    p6 = (x + size, y - size * 0.5)
    pygame.draw.polygon(WIN, COLORS['heart_red'], [p1, p2, p3, p4, p5, p6])


# --- SCENE IMPLEMENTATIONS (VIBES ONLY) ---

# CHAPTER 1: FIELD OF HOPES AND DREAMS
def init_ch1_field():
    elements = {'flora': [], 'trees': []}
    for _ in range(50):
        elements['flora'].append({ 'pos': (random.randint(0, SCREEN_WIDTH), random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT)), 'radius': random.randint(2, 5) })
    for _ in range(5):
        elements['trees'].append({ 'pos': (random.randint(0, SCREEN_WIDTH), random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT)), 'width': random.randint(80, 150) })
    return elements

def draw_ch1_field(elements, tick):
    WIN.fill(COLORS['dark_purple'])
    for f in elements['flora']:
        alpha = 150 + math.sin(tick * 0.05 + f['pos'][0]) * 100
        glow_surf = pygame.Surface((f['radius']*2, f['radius']*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLORS['glow_purple'], int(alpha)), (f['radius'], f['radius']), f['radius'])
        WIN.blit(glow_surf, (f['pos'][0] - f['radius'], f['pos'][1] - f['radius']))
    for t in elements['trees']:
        pygame.draw.rect(WIN, COLORS['plastic_brown'], (t['pos'][0] - 10, t['pos'][1] - 50, 20, 50))
        pygame.draw.circle(WIN, COLORS['spade_black'], (t['pos'][0], t['pos'][1] - 100), t['width'] // 2)
        pygame.draw.circle(WIN, COLORS['dark_purple'], (t['pos'][0], t['pos'][1] - 100), t['width'] // 2 - 10)
    draw_text("The Field of Hopes and Dreams", MENU_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 50)
    draw_text("VIBE: A forgotten playroom comes to life.", SCENE_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 100)

# CHAPTER 1: KING BOSS
def init_ch1_king():
    return {'spades': [], 'heart_pos': [SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.75]}

def draw_ch1_king(elements, tick):
    WIN.fill(COLORS['spade_black'])
    pygame.draw.rect(WIN, COLORS['king_gray'], (SCREEN_WIDTH // 2 - 100, 50, 200, 200))
    draw_text("KING", MENU_FONT, COLORS['white'], WIN, SCREEN_WIDTH/2, 150)
    if tick % 15 == 0:
        sfx_sounds['spade_shoot'].play()
        elements['spades'].append([random.randint(100, SCREEN_WIDTH-100), 250, random.randint(3, 6)])
    for spade in elements['spades']:
        spade[1] += spade[2]
        pygame.draw.circle(WIN, COLORS['white'], (spade[0], spade[1]), 10)
    elements['spades'] = [s for s in elements['spades'] if s[1] < SCREEN_HEIGHT]
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: elements['heart_pos'][0] -= 5
    if keys[pygame.K_RIGHT]: elements['heart_pos'][0] += 5
    if keys[pygame.K_UP]: elements['heart_pos'][1] -= 5
    if keys[pygame.K_DOWN]: elements['heart_pos'][1] += 5
    draw_heart(elements['heart_pos'][0], elements['heart_pos'][1], 15)
    draw_text("VIBE: Genuine menace. Dodge the attacks.", SCENE_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 30)

# CHAPTER 1: JEVIL BOSS
def init_ch1_jevil():
    return {'heart_pos': [SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.75], 'attacks': [], 'angle': 0}

def draw_ch1_jevil(elements, tick):
    WIN.fill(COLORS['black'])
    elements['angle'] = (elements['angle'] + 2) % 360
    # Draw spinning background
    for i in range(12):
        angle = math.radians(elements['angle'] + i * 30)
        x_start = SCREEN_WIDTH / 2
        y_start = SCREEN_HEIGHT / 2
        x_end = x_start + math.cos(angle) * 1000
        y_end = y_start + math.sin(angle) * 1000
        color = COLORS['jevil_purple'] if i % 2 == 0 else COLORS['jevil_yellow']
        pygame.draw.line(WIN, color, (x_start, y_start), (x_end, y_end), 50)
    # Generate attacks
    if tick % 10 == 0:
        attack_type = random.choice(['spade', 'diamond'])
        for i in range(5):
            elements['attacks'].append({
                'type': attack_type, 'pos': [random.randint(0, SCREEN_WIDTH), 0], 'angle': i * 72
            })
    # Draw attacks
    for attack in elements['attacks']:
        attack['pos'][1] += 5
        color = COLORS['white'] if attack['type'] == 'spade' else COLORS['heart_red']
        pygame.draw.circle(WIN, color, attack['pos'], 10)
    elements['attacks'] = [a for a in elements['attacks'] if a['pos'][1] < SCREEN_HEIGHT]
    # Draw player
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: elements['heart_pos'][0] -= 6
    if keys[pygame.K_RIGHT]: elements['heart_pos'][0] += 6
    if keys[pygame.K_UP]: elements['heart_pos'][1] -= 6
    if keys[pygame.K_DOWN]: elements['heart_pos'][1] += 6
    draw_heart(elements['heart_pos'][0], elements['heart_pos'][1], 15)
    draw_text("CHAOS, CHAOS!", MENU_FONT, random.choice(list(COLORS.values())), WIN, SCREEN_WIDTH / 2, 50)


# CHAPTER 2: CYBER CITY
def init_ch2_cyber():
    ads = []
    for _ in range(10):
        ads.append({
            'rect': pygame.Rect(random.randint(0, SCREEN_WIDTH-100), random.randint(0, SCREEN_HEIGHT-50), random.randint(100, 300), random.randint(50, 150)),
            'color': random.choice([COLORS['cyber_neon_pink'], COLORS['cyber_neon_green']]),
            'text': random.choice(['BUY!', 'CLICK!', 'FREE!', 'DEALS!']),
            'timer': random.randint(60, 180)
        })
    return {'ads': ads, 'grid_offset': 0}

def draw_ch2_cyber(elements, tick):
    WIN.fill(COLORS['black'])
    elements['grid_offset'] = (elements['grid_offset'] + 2) % 50
    for x in range(0, SCREEN_WIDTH, 50):
        pygame.draw.line(WIN, COLORS['cyber_grid'], (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(elements['grid_offset'] - 50, SCREEN_HEIGHT, 50):
        pygame.draw.line(WIN, COLORS['cyber_grid'], (0, y), (SCREEN_WIDTH, y), 1)
    for ad in elements['ads']:
        if ad['timer'] > 0:
            if ad['timer'] % 60 < 30:
                pygame.draw.rect(WIN, ad['color'], ad['rect'])
                draw_text(ad['text'], POPUP_FONT, COLORS['black'], WIN, ad['rect'].centerx, ad['rect'].centery)
            ad['timer'] -= 1
        else:
            ad['timer'] = random.randint(60, 240)
            ad['rect'].x = random.randint(0, SCREEN_WIDTH - 100)
            ad['rect'].y = random.randint(0, SCREEN_HEIGHT - 50)
    draw_text("Cyber City", MENU_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 50)
    draw_text("VIBE: Constant advertising and data overload.", SCENE_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 100)

# CHAPTER 2: QUEEN BOSS
def init_ch2_queen():
    return {'heart_pos': [SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.75], 'attacks': [], 'queen_y': -100}

def draw_ch2_queen(elements, tick):
    WIN.fill(COLORS['black'])
    # Queen entry animation
    if elements['queen_y'] < 50: elements['queen_y'] += 2
    # Draw Queen
    pygame.draw.rect(WIN, COLORS['queen_blue'], (SCREEN_WIDTH // 2 - 150, elements['queen_y'], 300, 150))
    pygame.draw.rect(WIN, COLORS['black'], (SCREEN_WIDTH // 2 - 140, elements['queen_y'] + 10, 280, 130))
    draw_text("LMAO", MENU_FONT, COLORS['white'], WIN, SCREEN_WIDTH/2, elements['queen_y'] + 75)
    # Generate attacks
    if tick % 40 == 0:
        elements['attacks'].append({
            'rect': pygame.Rect(random.randint(100, SCREEN_WIDTH - 200), 200, 150, 50),
            'text': "Potassium"
        })
    # Draw attacks
    for attack in elements['attacks']:
        attack['rect'].y += 4
        pygame.draw.rect(WIN, COLORS['queen_acid'], attack['rect'])
        draw_text(attack['text'], SCENE_FONT, COLORS['black'], WIN, attack['rect'].centerx, attack['rect'].centery)
    elements['attacks'] = [a for a in elements['attacks'] if a['rect'].y < SCREEN_HEIGHT]
    # Draw player
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: elements['heart_pos'][0] -= 5
    if keys[pygame.K_RIGHT]: elements['heart_pos'][0] += 5
    if keys[pygame.K_UP]: elements['heart_pos'][1] -= 5
    if keys[pygame.K_DOWN]: elements['heart_pos'][1] += 5
    draw_heart(elements['heart_pos'][0], elements['heart_pos'][1], 15)
    draw_text("Get The Banana", POPUP_FONT, COLORS['potassium_yellow'], WIN, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40)

# CHAPTER 2: SPAMTON NEO BOSS
def init_ch2_spamton():
    return {
        'strings': [(random.randint(200, SCREEN_WIDTH - 200), 0) for _ in range(4)],
        'head_pos': [SCREEN_WIDTH / 2, 150],
        'attacks': [],
        'glitch_timer': 0
    }

def draw_ch2_spamton(elements, tick):
    WIN.fill(COLORS['spam_basement'])
    head_pos_offset = (elements['head_pos'][0] + math.sin(tick*0.2)*20, elements['head_pos'][1] + math.cos(tick*0.25)*10)
    for s_pos in elements['strings']:
        pygame.draw.line(WIN, COLORS['glitch_static'], s_pos, head_pos_offset, 2)
    body_points = [
        (head_pos_offset[0] - 40, head_pos_offset[1] + 20 + math.sin(tick*0.3)*10),
        (head_pos_offset[0] + 40, head_pos_offset[1] + 20 + math.cos(tick*0.35)*10),
        (head_pos_offset[0], head_pos_offset[1] + 150 + math.sin(tick*0.4)*10) ]
    pygame.draw.polygon(WIN, random.choice([COLORS['spam_yellow'], COLORS['spam_pink'], COLORS['white']]), body_points)
    pygame.draw.circle(WIN, COLORS['black'], head_pos_offset, 20)
    if tick % 5 == 0:
        elements['attacks'].append(pygame.Rect(head_pos_offset[0], head_pos_offset[1], 10, 10))
    for attack in elements['attacks']:
        attack.x += random.randint(-5, 5)
        attack.y += random.randint(4, 8)
        draw_text("[[$]]", SPAMTON_FONT, COLORS['cyber_neon_green'], WIN, attack.centerx, attack.centery)
    elements['attacks'] = [a for a in elements['attacks'] if a.y < SCREEN_HEIGHT]
    if elements['glitch_timer'] > 0:
        if random.randint(0,2) == 0: sfx_sounds['glitch'].play()
        x_offset, y_offset = random.randint(-10, 10), random.randint(-10, 10)
        glitch_area = pygame.Rect(random.randint(0, SCREEN_WIDTH-200), random.randint(0, SCREEN_HEIGHT-200), 200, 200)
        WIN.blit(WIN, (glitch_area.x + x_offset, glitch_area.y + y_offset), glitch_area)
        elements['glitch_timer'] -= 1
    if random.randint(0, 30) == 0:
        elements['glitch_timer'] = 5
    draw_text("[BIG SHOT] VIBE", MENU_FONT, COLORS['spam_yellow'], WIN, SCREEN_WIDTH / 2, 50)
    draw_text("A desperate, glitching puppet on strings.", SCENE_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 100)


# --- MAIN GAME CONTROLLER ---
def main():
    """The main loop that manages states."""
    init_audio() # Generate all sounds at launch
    current_state = "MENU"
    menu_selection = 0
    menu_options = ["CH1: Field", "CH1: King", "CH1: Jevil", "CH2: Cyber City", "CH2: Queen", "CH2: Spamton"]
    scene_funcs = {
        "CH1: Field": (init_ch1_field, draw_ch1_field),
        "CH1: King": (init_ch1_king, draw_ch1_king),
        "CH1: Jevil": (init_ch1_jevil, draw_ch1_jevil),
        "CH2: Cyber City": (init_ch2_cyber, draw_ch2_cyber),
        "CH2: Queen": (init_ch2_queen, draw_ch2_queen),
        "CH2: Spamton": (init_ch2_spamton, draw_ch2_spamton)
    }
    tick = 0
    
    # Start menu music
    pygame.mixer.stop()
    music_tracks["MENU"].play(loops=-1)

    while True:
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if current_state == "MENU":
                    if event.key == pygame.K_DOWN:
                        menu_selection = (menu_selection + 1) % len(menu_options)
                        sfx_sounds['menu_move'].play()
                    if event.key == pygame.K_UP:
                        menu_selection = (menu_selection - 1) % len(menu_options)
                        sfx_sounds['menu_move'].play()
                    if event.key == pygame.K_RETURN:
                        sfx_sounds['menu_select'].play()
                        current_state = menu_options[menu_selection]
                        # Initialize scene if not already initialized
                        if current_state not in scene_elements:
                            init_func, _ = scene_funcs[current_state]
                            scene_elements[current_state] = init_func()
                        tick = 0 # Reset tick counter for new scene
                        # Change music
                        pygame.mixer.stop()
                        if current_state in music_tracks:
                            music_tracks[current_state].play(loops=-1)
                else: # In a scene
                    if event.key == pygame.K_ESCAPE:
                        current_state = "MENU"
                        pygame.mixer.stop()
                        music_tracks["MENU"].play(loops=-1)

        # --- DRAWING ---
        if current_state == "MENU":
            WIN.fill(COLORS['black'])
            draw_text("VIBE BROWSER", MENU_FONT, COLORS['white'], WIN, SCREEN_WIDTH / 2, 100)
            for i, option in enumerate(menu_options):
                color = COLORS['spam_yellow'] if i == menu_selection else COLORS['white']
                draw_text(option, MENU_FONT, color, WIN, SCREEN_WIDTH / 2, 220 + i * 70)
            draw_text("Use arrows and Enter. Press ESC in a scene to return.", SCENE_FONT, COLORS['white'], WIN, SCREEN_WIDTH/2, SCREEN_HEIGHT - 50)
        else:
            _, draw_func = scene_funcs[current_state]
            draw_func(scene_elements[current_state], tick)

        # --- UPDATE ---
        pygame.display.flip()
        CLOCK.tick(FPS)
        tick += 1

if __name__ == "__main__":
    main()
