"""
Audio Analyzer für DJ-Performance Videos.
Erkennt Beat Drops, Buildups, Energie-Spitzen und Transitions.
"""

import numpy as np
import librosa
import subprocess
import os
import tempfile
import config


def extract_audio(video_path, output_path=None):
    """Extrahiert Audio aus einem Video als WAV-Datei."""
    if output_path is None:
        output_path = os.path.join(
            config.TEMP_DIR,
            os.path.splitext(os.path.basename(video_path))[0] + ".wav"
        )

    if os.path.exists(output_path):
        return output_path

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",  # kein Video
        "-acodec", "pcm_s16le",
        "-ar", str(config.AUDIO_SAMPLE_RATE),
        "-ac", "1",  # Mono
        "-y",  # Überschreiben
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
    except subprocess.TimeoutExpired:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(f"FFmpeg Timeout bei Audio-Extraktion (>120s): {video_path}")
    except subprocess.CalledProcessError as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(
            f"FFmpeg Fehler bei Audio-Extraktion: "
            f"{e.stderr.decode(errors='replace')[:300]}"
        )
    return output_path


def analyze_audio(video_path, progress_callback=None):
    """
    Führt vollständige Audio-Analyse durch.
    
    Returns:
        dict mit:
        - tempo: BPM
        - beat_times: Array von Beat-Zeitpunkten in Sekunden
        - energy_envelope: Onset-Strength über Zeit
        - energy_times: Zeitstempel für energy_envelope
        - energy_peaks: Zeitpunkte von Energie-Spitzen
        - bass_drops: Liste von {time, intensity} Bass-Drop-Events
        - buildups: Liste von {start, end, intensity} Buildup-Bereiche
        - breakdowns: Liste von {start, end} Breakdown-Bereiche
        - duration: Gesamtdauer in Sekunden
    """
    if progress_callback:
        progress_callback("audio", 0, "Audio wird extrahiert...")

    # Audio extrahieren
    audio_path = extract_audio(video_path)

    if progress_callback:
        progress_callback("audio", 15, "Audio wird geladen...")

    # Audio laden
    y, sr = librosa.load(audio_path, sr=config.AUDIO_SAMPLE_RATE)
    duration = librosa.get_duration(y=y, sr=sr)

    if progress_callback:
        progress_callback("audio", 25, "Beats werden erkannt...")

    # --- Beat Detection ---
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    # tempo kann ein Array sein in neueren librosa-Versionen
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=config.HOP_LENGTH)

    if progress_callback:
        progress_callback("audio", 40, "Energie wird analysiert...")

    # --- Energy/Onset Strength ---
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    energy_times = librosa.times_like(onset_env, sr=sr, hop_length=config.HOP_LENGTH)

    # Normalisieren
    if onset_env.max() > 0:
        onset_env_norm = onset_env / onset_env.max()
    else:
        onset_env_norm = onset_env

    # Energie-Peaks finden
    threshold = np.percentile(onset_env_norm, config.ENERGY_THRESHOLD_PERCENTILE)
    peak_indices = _find_peaks(onset_env_norm, threshold, min_distance_frames=int(sr / config.HOP_LENGTH * 0.5))
    energy_peaks = energy_times[peak_indices] if len(peak_indices) > 0 else np.array([])

    if progress_callback:
        progress_callback("audio", 55, "Bass Drops werden erkannt...")

    # --- Bass Drop Detection ---
    bass_drops = _detect_bass_drops(y, sr, energy_times)

    if progress_callback:
        progress_callback("audio", 70, "Buildups werden erkannt...")

    # --- Buildup / Breakdown Detection ---
    buildups, breakdowns = _detect_buildups_breakdowns(onset_env_norm, energy_times)

    if progress_callback:
        progress_callback("audio", 90, "Audio-Analyse abgeschlossen")

    results = {
        "tempo": tempo,
        "beat_times": beat_times.tolist(),
        "energy_envelope": onset_env_norm.tolist(),
        "energy_times": energy_times.tolist(),
        "energy_peaks": energy_peaks.tolist(),
        "bass_drops": bass_drops,
        "buildups": buildups,
        "breakdowns": breakdowns,
        "duration": duration,
    }

    if progress_callback:
        progress_callback("audio", 100, "Audio-Analyse fertig")

    # WAV-Datei nach erfolgreicher Analyse löschen (kein Nutzen als Cache,
    # da Ergebnisse in _analysis.json persistiert werden)
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except OSError:
        pass  # Nicht-kritisch – nächster Lauf extrahiert neu

    return results


def _find_peaks(signal, threshold, min_distance_frames=10):
    """Findet Peaks in einem Signal über einem Schwellenwert."""
    peaks = []
    i = 1
    while i < len(signal) - 1:
        if signal[i] > threshold and signal[i] > signal[i - 1] and signal[i] >= signal[i + 1]:
            peaks.append(i)
            i += min_distance_frames  # Mindestabstand
        else:
            i += 1
    return np.array(peaks)


def _detect_bass_drops(y, sr, energy_times):
    """Erkennt Bass Drops durch Analyse der tiefen Frequenzen."""
    bass_drops = []

    # Mel-Spektrogramm berechnen
    S = librosa.feature.melspectrogram(
        y=y, sr=sr,
        hop_length=config.HOP_LENGTH,
        n_mels=128,
        fmax=sr // 2
    )

    # Nur Bass-Frequenzen (untere Mel-Bänder, ca. < 200Hz)
    mel_freqs = librosa.mel_frequencies(n_mels=128, fmax=sr // 2)
    bass_mask = mel_freqs < config.BASS_FREQ_MAX
    bass_energy = np.sum(S[bass_mask], axis=0)

    # Normalisieren
    if bass_energy.max() > 0:
        bass_norm = bass_energy / bass_energy.max()
    else:
        return bass_drops

    # Zeitachse
    times = librosa.times_like(bass_norm, sr=sr, hop_length=config.HOP_LENGTH)

    # Bass Drops finden: plötzlicher Anstieg der Bass-Energie
    window_frames = int(config.BUILDUP_WINDOW_SEC * sr / config.HOP_LENGTH)

    for i in range(window_frames, len(bass_norm) - 1):
        # Vergleiche aktuelle Bass-Energie mit dem Durchschnitt der letzten Sekunden
        preceding_mean = np.mean(bass_norm[max(0, i - window_frames):i])
        if preceding_mean > 0:
            ratio = bass_norm[i] / preceding_mean
            if ratio >= config.MIN_DROP_ENERGY_RATIO and bass_norm[i] > 0.5:
                # Prüfe ob nicht zu nah am letzten Drop
                if len(bass_drops) == 0 or (times[i] - bass_drops[-1]["time"]) > 4.0:
                    bass_drops.append({
                        "time": float(times[i]),
                        "intensity": float(min(ratio / 4.0, 1.0))  # Normalisiert 0-1
                    })

    return bass_drops


def analyze_music_file(music_path: str) -> dict:
    """
    Analysiert eine eigenständige Audiodatei (mp3/wav/flac/aif/aiff)
    auf Bass, Subbass, Kicks, Transienten und Drops.
    
    Returns:
        dict with:
        - subbass_energy: Liste von (time, energy) für 20-60 Hz
        - bass_energy: Liste von (time, energy) für 60-250 Hz
        - kick_times: Liste von Zeitpunkten in Sekunden (Kick-Onsets)
        - transient_times: Liste von Zeitpunkten in Sekunden (Transienten)
        - drop_times: Liste von {time, intensity} für Bass-Drops
        - duration: Dauer in Sekunden
        - sample_rate: verwendete Abtastrate
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(music_path, sr=config.AUDIO_SAMPLE_RATE)
    duration = librosa.get_duration(y=y, sr=sr)

    # Mel-Spektrogramm für Frequenzbänder
    S = librosa.feature.melspectrogram(
        y=y, sr=sr,
        hop_length=config.HOP_LENGTH,
        n_mels=128,
        fmax=sr // 2
    )
    times = librosa.times_like(S, sr=sr, hop_length=config.HOP_LENGTH)

    # Frequenzbänder in Mel-Skala
    mel_freqs = librosa.mel_frequencies(n_mels=128, fmax=sr // 2)

    # Subbass: 20-60 Hz
    subbass_mask = (mel_freqs >= 20) & (mel_freqs < 60)
    subbass_energy = np.sum(S[subbass_mask], axis=0) if np.any(subbass_mask) else np.zeros(S.shape[1])
    subbass_norm = subbass_energy / (subbass_energy.max() + 1e-6)

    # Bass: 60-250 Hz
    bass_mask = (mel_freqs >= 60) & (mel_freqs < 250)
    bass_energy = np.sum(S[bass_mask], axis=0) if np.any(bass_mask) else np.zeros(S.shape[1])
    bass_norm = bass_energy / (bass_energy.max() + 1e-6)

    # Kick-Detektion: tiefe Frequenz (Subbass+Bass) + onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=config.HOP_LENGTH)
    onset_env_norm = onset_env / (onset_env.max() + 1e-6)

    # Kombinierte Kick-Energie (Subbass + onset)
    kick_energy = 0.6 * subbass_norm + 0.4 * onset_env_norm
    kick_threshold = np.percentile(kick_energy, 85)
    kick_peaks = _find_peaks2(kick_energy, kick_threshold, min_distance_frames=int(0.1 * sr / config.HOP_LENGTH))
    kick_times = times[kick_peaks].tolist() if len(kick_peaks) > 0 else []

    # Transienten: schnelle Anstiege im onset envelope (high-frequency content)
    transient_threshold = np.percentile(onset_env_norm, 90)
    trans_peaks = _find_peaks2(onset_env_norm, transient_threshold, min_distance_frames=int(0.05 * sr / config.HOP_LENGTH))
    transient_times = times[trans_peaks].tolist() if len(trans_peaks) > 0 else []

    # Drop-Detektion: steiler Anstieg der Bass-Energie (ähnlich _detect_bass_drops)
    drops = _detect_drops(bass_norm, times, sr)

    # Energie-Kurven als Listen von (time, value)
    subbass_list = [(float(times[i]), float(subbass_norm[i])) for i in range(len(times))]
    bass_list = [(float(times[i]), float(bass_norm[i])) for i in range(len(times))]

    return {
        "subbass_energy": subbass_list,
        "bass_energy": bass_list,
        "kick_times": kick_times,
        "transient_times": transient_times,
        "drop_times": drops,
        "duration": duration,
        "sample_rate": sr,
    }


def _find_peaks2(signal: np.ndarray, threshold: float, min_distance_frames: int = 10) -> np.ndarray:
    """Findet Peaks in einem 1D-Signal (einfach, kein scipy)."""
    peaks = []
    i = 1
    while i < len(signal) - 1:
        if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] >= signal[i+1]:
            peaks.append(i)
            i += min_distance_frames
        else:
            i += 1
    return np.array(peaks)


def _detect_drops(bass_energy: np.ndarray, times: np.ndarray, sr: int) -> list:
    """
    Erkennt Drops als plötzlichen Anstieg der Bass-Energie.
    Gibt Liste von {time, intensity} zurück.
    """
    drops = []
    window_frames = int(1.0 * sr / config.HOP_LENGTH)  # 1 Sekunde Vergangenheit
    for i in range(window_frames, len(bass_energy) - 1):
        preceding_mean = np.mean(bass_energy[max(0, i - window_frames):i])
        if preceding_mean > 0 and bass_energy[i] > 0.5:
            ratio = bass_energy[i] / preceding_mean
            if ratio >= 2.0:  # Faktor 2 Anstieg
                # Abstand zu letztem Drop > 4 sec
                if len(drops) == 0 or (times[i] - drops[-1]["time"]) > 4.0:
                    drops.append({
                        "time": float(times[i]),
                        "intensity": float(min(ratio / 4.0, 1.0))
                    })
    return drops


def _detect_buildups_breakdowns(onset_env_norm, energy_times):
    """
    Erkennt Buildups (steigende Energie) und Breakdowns (fallende Energie).
    """
    buildups = []
    breakdowns = []

    # Glätten der Energie-Kurve
    window_size = 50  # Frames
    if len(onset_env_norm) < window_size * 2:
        return buildups, breakdowns

    smoothed = np.convolve(onset_env_norm, np.ones(window_size) / window_size, mode='same')

    # Gradient berechnen
    gradient = np.gradient(smoothed)

    # Positive Gradienten-Regionen = Buildups
    buildup_threshold = np.percentile(gradient[gradient > 0], 70) if np.any(gradient > 0) else 0.001
    breakdown_threshold = np.percentile(gradient[gradient < 0], 30) if np.any(gradient < 0) else -0.001

    # Zusammenhängende Regionen finden
    in_buildup = False
    buildup_start = 0

    for i in range(len(gradient)):
        if gradient[i] > buildup_threshold and not in_buildup:
            in_buildup = True
            buildup_start = i
        elif gradient[i] <= buildup_threshold * 0.5 and in_buildup:
            in_buildup = False
            start_time = float(energy_times[buildup_start])
            end_time = float(energy_times[min(i, len(energy_times) - 1)])
            duration = end_time - start_time
            if duration >= 2.0:  # Mindestens 2 Sekunden
                intensity = float(np.mean(gradient[buildup_start:i]) / max(buildup_threshold, 0.001))
                buildups.append({
                    "start": start_time,
                    "end": end_time,
                    "intensity": min(intensity, 1.0)
                })

    # Breakdowns: plötzlicher Energieabfall
    in_breakdown = False
    breakdown_start = 0

    for i in range(len(gradient)):
        if gradient[i] < breakdown_threshold and not in_breakdown:
            in_breakdown = True
            breakdown_start = i
        elif gradient[i] >= breakdown_threshold * 0.5 and in_breakdown:
            in_breakdown = False
            start_time = float(energy_times[breakdown_start])
            end_time = float(energy_times[min(i, len(energy_times) - 1)])
            duration = end_time - start_time
            if duration >= 1.0:
                breakdowns.append({
                    "start": start_time,
                    "end": end_time,
                })

    return buildups, breakdowns
