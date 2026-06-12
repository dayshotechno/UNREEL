/**
 * UNREEL – PRODUCTION UTILITY v2.0
 * Pure Techno Aesthetic - Brutalist / Industrial
 */

// ============================================
// STATE
// ============================================
const state = {
    videos: [],
    currentVideo: null,
    analysisResults: null,
    suggestedClips: [],
    selectedClips: new Set(),
    currentPresetFilter: 'all',
    exportMode: 'reel',
    pollInterval: null,
    activeExportJobId: null,   // job_id des laufenden Exports (für Cancel)
};

// ============================================
// DOM REFERENCES
// ============================================
const dom = {
    // Views
    libraryView: document.getElementById('libraryView'),
    analysisView: document.getElementById('analysisView'),
    // Header
    videoCount: document.getElementById('videoCount'),

    // Tabs

    // Library
    videoGrid: document.getElementById('videoGrid'),
    emptyLibrary: document.getElementById('emptyLibrary'),
    exportBestOfSetBtn: document.getElementById('exportBestOfSetBtn'),
    resetUsageLogBtn: document.getElementById('resetUsageLogBtn'),
    // BPM Tempo-Match
    bpmControl: document.getElementById('bpmControl'),
    bpmMatchToggle: document.getElementById('bpmMatchToggle'),
    bpmSlider: document.getElementById('bpmSlider'),
    bpmValue: document.getElementById('bpmValue'),
    globalBestOf15Btn: document.getElementById('globalBestOf15Btn'),
    globalBestOf30Btn: document.getElementById('globalBestOf30Btn'),
    globalBestOf45Btn: document.getElementById('globalBestOf45Btn'),
    globalBestOf90Btn: document.getElementById('globalBestOf90Btn'),
    highlightArc15Btn: document.getElementById('highlightArc15Btn'),
    highlightArc30Btn: document.getElementById('highlightArc30Btn'),
    highlightArc45Btn: document.getElementById('highlightArc45Btn'),
    highlightArc90Btn: document.getElementById('highlightArc90Btn'),
    chronoArc15Btn: document.getElementById('chronoArc15Btn'),
    chronoArc30Btn: document.getElementById('chronoArc30Btn'),
    chronoArc45Btn: document.getElementById('chronoArc45Btn'),
    chronoArc90Btn: document.getElementById('chronoArc90Btn'),
    randomArc15Btn: document.getElementById('randomArc15Btn'),
    randomArc30Btn: document.getElementById('randomArc30Btn'),
    randomArc45Btn: document.getElementById('randomArc45Btn'),
    adaptiveArc15Btn: document.getElementById('adaptiveArc15Btn'),
    adaptiveArc30Btn: document.getElementById('adaptiveArc30Btn'),
    adaptiveArc45Btn: document.getElementById('adaptiveArc45Btn'),
    bpmLocked15Btn: document.getElementById('bpmLocked15Btn'),
    bpmLocked30Btn: document.getElementById('bpmLocked30Btn'),
    bpmLocked45Btn: document.getElementById('bpmLocked45Btn'),
    strobeMontage15Btn: document.getElementById('strobeMontage15Btn'),
    strobeMontage30Btn: document.getElementById('strobeMontage30Btn'),
    strobeMontage45Btn: document.getElementById('strobeMontage45Btn'),
    crowdCulture15Btn: document.getElementById('crowdCulture15Btn'),
    crowdCulture30Btn: document.getElementById('crowdCulture30Btn'),
    crowdCulture45Btn: document.getElementById('crowdCulture45Btn'),
    loopReel8Btn: document.getElementById('loopReel8Btn'),
    loopReel15Btn: document.getElementById('loopReel15Btn'),
    dropArchitectureBtn: document.getElementById('dropArchitectureBtn'),
    transitionMastery30Btn: document.getElementById('transitionMastery30Btn'),
    transitionMastery45Btn: document.getElementById('transitionMastery45Btn'),
    storyArcBtn: document.getElementById('storyArcBtn'),
    wmBatchCleanBtn: document.getElementById('wmBatchCleanBtn'),

    // Production / Studio
    analysisVideoName: document.getElementById('analysisVideoName'),
    backToLibrary: document.getElementById('backToLibrary'),
    videoPlayer: document.getElementById('videoPlayer'),
    videoSource: document.getElementById('videoSource'),
    statsRow: document.getElementById('statsRow'),
    timelineSection: document.getElementById('timelineSection'),
    clipsPanel: document.getElementById('clipsPanel'),
    timelineCanvas: document.getElementById('timelineCanvas'),
    timelineWrapper: document.getElementById('timelineWrapper'),
    playhead: document.getElementById('playhead'),
    clipsList: document.getElementById('clipsList'),
    clipCountBadge: document.getElementById('clipCountBadge'),
    presetTabs: document.getElementById('presetTabs'),
    autoSelect15: document.getElementById('autoSelect15'),
    autoSelect30: document.getElementById('autoSelect30'),

    // Stats
    statTempo: document.getElementById('statTempo'),
    statDuration: document.getElementById('statDuration'),
    statHighlights: document.getElementById('statHighlights'),
    statDrops: document.getElementById('statDrops'),
    statClips: document.getElementById('statClips'),

    // Time labels
    timeStart: document.getElementById('timeStart'),
    timeMid: document.getElementById('timeMid'),
    timeEnd: document.getElementById('timeEnd'),

    // Export
    exportModeReel: document.getElementById('exportModeReel'),
    exportModeRaw: document.getElementById('exportModeRaw'),
    fadeToggle: document.getElementById('fadeToggle'),
    exportSelectedBtn: document.getElementById('exportSelectedBtn'),
    exportAllBtn: document.getElementById('exportAllBtn'),

    // Watermark
    wmScanBtn:  document.getElementById('wmScanBtn'),
    wmResult:   document.getElementById('wmResult'),
    wmRemoveBtn: document.getElementById('wmRemoveBtn'),

    // Progress
    progressOverlay: document.getElementById('progressOverlay'),
    progressTitle: document.getElementById('progressTitle'),
    progressMessage: document.getElementById('progressMessage'),
    progressBarFill: document.getElementById('progressBarFill'),
    progressPercentage: document.getElementById('progressPercentage'),

    // Toast
    toastContainer: document.getElementById('toastContainer'),

    // Cancel
    progressCancelBtn: document.getElementById('progressCancelBtn'),
};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    initFunctionTooltips();
    loadVideos();

    // Auto-refresh library
    setInterval(loadVideos, 30000);
});

function initEventListeners() {
    // Back button
    dom.backToLibrary.addEventListener('click', () => switchView('library'));

    // Watermark
    dom.wmScanBtn.addEventListener('click', runWatermarkScan);
    dom.wmRemoveBtn.addEventListener('click', removeWatermark);

    // Global Best-Of
    dom.globalBestOf15Btn.addEventListener('click', () => createGlobalBestOf(15));
    dom.globalBestOf30Btn.addEventListener('click', () => createGlobalBestOf(30));
    dom.globalBestOf45Btn.addEventListener('click', () => createGlobalBestOf(45));
    dom.globalBestOf90Btn?.addEventListener('click', () => createGlobalBestOf(90));

    // Highlight Arcs
    dom.highlightArc15Btn.addEventListener('click', () => createHighlightArc(15));
    dom.highlightArc30Btn.addEventListener('click', () => createHighlightArc(30));
    dom.highlightArc45Btn.addEventListener('click', () => createHighlightArc(45));
    dom.highlightArc90Btn?.addEventListener('click', () => createHighlightArc(90));

    // Chrono Arcs
    dom.chronoArc15Btn.addEventListener('click', () => createChronologicalReel(15));
    dom.chronoArc30Btn.addEventListener('click', () => createChronologicalReel(30));
    dom.chronoArc45Btn.addEventListener('click', () => createChronologicalReel(45));
    dom.chronoArc90Btn?.addEventListener('click', () => createChronologicalReel(90));

    // Random Arcs
    dom.randomArc15Btn.addEventListener('click', () => createRandomReel(15));
    dom.randomArc30Btn.addEventListener('click', () => createRandomReel(30));
    dom.randomArc45Btn.addEventListener('click', () => createRandomReel(45));

    // SEAMLESS LOOP
    dom.loopReel8Btn?.addEventListener('click', () => createSeamlessLoop(8));
    dom.loopReel15Btn?.addEventListener('click', () => createSeamlessLoop(15));
    
    // DROP ARCHITECTURE
    dom.dropArchitectureBtn?.addEventListener('click', () => createDropArchitecture(15));

    // TRANSITION MASTERY
    dom.transitionMastery30Btn?.addEventListener('click', () => createTransitionMastery(30));
    dom.transitionMastery45Btn?.addEventListener('click', () => createTransitionMastery(45));

    // WM CLEANUP
    dom.wmBatchCleanBtn?.addEventListener('click', batchCleanWatermarks);

    // Best-Of Set (Individual Clips)
    dom.exportBestOfSetBtn.addEventListener('click', createBestOfSet);

    // Rotation Reset
    dom.resetUsageLogBtn.addEventListener('click', resetUsageLog);

    // Adaptive Arc
    dom.adaptiveArc15Btn.addEventListener('click', () => createAdaptiveReel(15));
    dom.adaptiveArc30Btn.addEventListener('click', () => createAdaptiveReel(30));
    dom.adaptiveArc45Btn.addEventListener('click', () => createAdaptiveReel(45));

    // BPM Lock
    dom.bpmLocked15Btn.addEventListener('click', () => createBpmLockedReel(15));
    dom.bpmLocked30Btn.addEventListener('click', () => createBpmLockedReel(30));
    dom.bpmLocked45Btn.addEventListener('click', () => createBpmLockedReel(45));

    // Strobe Montage
    dom.strobeMontage15Btn.addEventListener('click', () => createStrobeMontage(15));
    dom.strobeMontage30Btn.addEventListener('click', () => createStrobeMontage(30));
    dom.strobeMontage45Btn.addEventListener('click', () => createStrobeMontage(45));

    // Crowd Culture
    dom.crowdCulture15Btn.addEventListener('click', () => createCrowdCulture(15));
    dom.crowdCulture30Btn.addEventListener('click', () => createCrowdCulture(30));
    dom.crowdCulture45Btn.addEventListener('click', () => createCrowdCulture(45));

    // Story Arc
    dom.storyArcBtn.addEventListener('click', createStoryArc);

    // WM Batch Clean
    dom.wmBatchCleanBtn.addEventListener('click', batchCleanWatermarks);

    // BPM Tempo-Match Regler
    dom.bpmMatchToggle.addEventListener('change', onBpmToggle);
    dom.bpmSlider.addEventListener('input', updateBpmLabel);

    // Preset filter tabs
    dom.presetTabs.addEventListener('click', (e) => {
        const tab = e.target.closest('.preset-tab');
        if (tab) {
            document.querySelectorAll('.preset-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.currentPresetFilter = tab.dataset.preset;
            renderClipsList();
        }
    });

    // Auto-Select buttons
    dom.autoSelect15.addEventListener('click', () => autoSelectTransitionReel(15));
    dom.autoSelect30.addEventListener('click', () => autoSelectTransitionReel(30));

    // Export mode toggle
    dom.exportModeReel.addEventListener('click', () => setExportMode('reel'));
    dom.exportModeRaw.addEventListener('click', () => setExportMode('raw'));

    // Export buttons
    dom.exportSelectedBtn.addEventListener('click', exportSelected);
    dom.exportAllBtn.addEventListener('click', exportAll);

    // Cancel export
    dom.progressCancelBtn.addEventListener('click', cancelCurrentExport);

    // Video player time update → playhead
    dom.videoPlayer.addEventListener('timeupdate', updatePlayhead);

    // Timeline click → seek
    dom.timelineWrapper.addEventListener('click', (e) => {
        if (!state.analysisResults) return;
        const rect = dom.timelineWrapper.getBoundingClientRect();
        const pct = (e.clientX - rect.left) / rect.width;
        const duration = state.analysisResults.audio.duration || dom.videoPlayer.duration;
        dom.videoPlayer.currentTime = pct * duration;
    });
}

// ============================================
// VIEW SWITCHING
// ============================================
function switchView(view) {
    dom.libraryView.style.display = 'none';
    dom.analysisView.classList.remove('active');
    switch (view) {
        case 'library':
            dom.libraryView.style.display = 'block';
            loadVideos();
            break;
        case 'analysis':
            dom.analysisView.classList.add('active');
            break;
    }
}

// ============================================
// VIDEO LIBRARY
// ============================================
async function loadVideos() {
    try {
        const resp = await fetch('/api/videos');
        const data = await resp.json();
        state.videos = data.videos || [];
        dom.videoCount.textContent = state.videos.length;
        renderVideoGrid();
    } catch (err) {
        console.error('Fehler beim Laden der Videos:', err);
    }
}

async function createGlobalBestOf(duration) {
    if (!confirm(`Möchtest du eine ${duration}s Montage aus den besten Momenten ALLER Videos erstellen?`)) return;

    showProgress('GLOBAL BEST-OF WIRD ERSTELLT...', 'DIE BESTEN MOMENTE WERDEN GESAMMELT...');

    try {
        const resp = await fetch('/api/export/global_best_of', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                duration: duration,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });

        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('GLOBAL BEST-OF FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createHighlightArc(duration) {
    if (!confirm(`Möchtest du ein ${duration}s Highlight-Arc Reel (mit Energie-Aufbau) aus ALLEN Videos erstellen?`)) return;

    showProgress('HIGHLIGHT ARC WIRD ERSTELLT...', 'CLIPS WERDEN NACH ENERGIE SORTIERT...');

    try {
        const resp = await fetch('/api/export/highlight_reel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                duration: duration,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });

        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('HIGHLIGHT ARC FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createChronologicalReel(duration) {
    if (!confirm(`Möchtest du eine ${duration}s lange chronologische Montage aus ALLEN Videos erstellen?`)) return;

    showProgress('CHRONOLOGISCHES REEL WIRD ERSTELLT...', 'CLIPS WERDEN NACH AUFNAHMEDATUM SORTIERT...');

    try {
        const resp = await fetch('/api/export/chronological_reel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                duration: duration,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });

        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('CHRONO REEL FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createRandomReel(duration) {
    if (!confirm(`Möchtest du eine ${duration}s lange Montage aus ZUFÄLLIGEN Clips erstellen?`)) return;

    showProgress('ZUFÄLLIGES REEL WIRD ERSTELLT...', 'CLIPS WERDEN DURCHGEMISCHT...');

    try {
        const resp = await fetch('/api/export/random_reel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                duration: duration,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });

        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('RANDOM REEL FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createSeamlessLoopReel(duration) {
    if (!confirm(`Möchtest du einen perfekten Seamless Loop (${duration}s) aus dem besten Clip erstellen?`)) return;

    showProgress('SEAMLESS LOOP WIRD ERSTELLT...', 'SUCHE DEN BESTEN CLIP FÜR DEN LOOP...');

    try {
        const resp = await fetch('/api/export/seamless_loop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                duration: duration,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });

        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('LOOP REEL FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createBestOfSet() {
    if (!confirm(
        'SMART PICK – 30 Clips als Einzeldateien\n\n' +
        'Intelligente Mischung aus Moment-Typen (DROP / CROWD / STROBE / CALM …),\n' +
        'verschiedenen Videos und Clip-Längen – frisch bei jedem Lauf, ohne Dubletten.\n' +
        'Dateinamen zeigen Typ + Tier (z. B. 01_DROP_S_…) für CapCut/Resolve.\n\n' +
        'Perfekt für den manuellen Schnitt. Fortfahren?'
    )) return;

    showProgress('BEST-OF SET WIRD EXPORTIERT...', 'DIE BESTEN EINZELCLIPS WERDEN VORBEREITET...');

    try {
        const resp = await fetch('/api/export/best_of_set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                count: 30,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });

        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 30);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('SET-EXPORT FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createAdaptiveReel(duration) {
    if (!confirm(
        `ADAPTIVE ARC – ${duration}s\n\n` +
        'Clip-Längen passen sich automatisch an den Energie-Score an:\n' +
        '  Niedrige Energie  →  lange Clips  (ruhiger Einstieg)\n' +
        '  Mittlere Energie  →  mittlere Cuts\n' +
        '  Hohe Energie      →  kurze Schnitte  (Climax)\n\n' +
        'Reihenfolge: Calm → Climax Arc aus allen analysierten Videos.\nFortfahren?'
    )) return;

    showProgress('ADAPTIVE ARC WIRD ERSTELLT...', 'ENERGIE-KURVE WIRD BERECHNET...');

    try {
        const resp = await fetch('/api/export/adaptive_reel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, mode: state.exportMode, target_bpm: getTargetBpm() }),
        });
        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            if (data.clips != null) {
                const range = data.beat_range ? ` · ${data.beat_range[0]}–${data.beat_range[1]} BEATS` : '';
                updateProgress(0, `${data.clips} CLIPS${range} · ~${data.actual_duration}S`);
            }
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('ADAPTIVE ARC FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createBpmLockedReel(duration) {
    if (!confirm(
        `BPM-LOCKED REEL – ${duration}s\n\n` +
        'Alle Schnittpunkte liegen exakt auf dem Beat.\n' +
        'Clip-Längen werden auf Bar-Vielfache (4 Beats) gerundet.\n\n' +
        'Clips aus allen analysierten Videos werden verwendet.\nFortfahren?'
    )) return;

    showProgress('BPM-LOCKED REEL WIRD ERSTELLT...', 'BEAT-GRID WIRD BERECHNET...');

    try {
        const resp = await fetch('/api/export/bpm_locked_reel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, mode: state.exportMode, target_bpm: getTargetBpm() }),
        });
        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            if (data.clips != null) {
                updateProgress(0, `${data.clips} CLIPS / ${data.total_bars} BARS / ~${data.actual_duration}S`);
            }
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('BPM-LOCKED REEL FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createStrobeMontage(duration) {
    if (!confirm(`Möchtest du eine ${duration}s lange Strobe Montage (harte Schnitte auf den Beat) erstellen?`)) return;

    showProgress('STROBE MONTAGE WIRD ERSTELLT...', 'BEAT-SAMPLES WERDEN EXTRAHIERT...');

    try {
        const resp = await fetch('/api/export/strobe_montage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, mode: state.exportMode, target_bpm: getTargetBpm() }),
        });
        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('STROBE MONTAGE FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createCrowdCulture(duration) {
    if (!confirm(`Möchtest du eine ${duration}s lange Crowd & Culture Montage (Jubel und Crowd-Reaktionen) erstellen?`)) return;

    showProgress('CROWD & CULTURE WIRD ERSTELLT...', 'CROWD-REAKTIONEN WERDEN GESAMMELT...');

    try {
        const resp = await fetch('/api/export/crowd_culture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, mode: state.exportMode, target_bpm: getTargetBpm() }),
        });
        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('CROWD & CULTURE FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createStoryArc() {
    if (!confirm(
        'STORY ARC RENDER\n\n' +
        '1. HOOK + BUILD-UP  –  Spannung aufbauen\n' +
        '2. DROP             –  Der Moment der Entladung\n' +
        '3. CROWD REACTION   –  Unmittelbare Reaktion\n' +
        '4. OUTRO            –  Letzter Eindruck\n\n' +
        'Clip-Auswahl erfolgt automatisch aus allen analysierten Videos.\nFortfahren?'
    )) return;

    showProgress('STORY ARC WIRD GERENDERT...', 'SEGMENTE WERDEN ANALYSIERT...');

    try {
        const resp = await fetch('/api/export/story_arc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: state.exportMode, target_bpm: getTargetBpm() }),
        });
        const data = await resp.json();

        if (data.status === 'started' && data.job_id) {
            // Zeige die erkannten Segmente im Progress-Dialog
            if (data.segments?.length) {
                updateProgress(0, 'SEGMENTE: ' + data.segments.join(' → '));
            }
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('STORY ARC FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createDropArchitecture(duration) {
    if (!confirm(`Möchtest du eine ${duration}s lange Drop Architecture Montage (exakt 3s vor dem größten Drop) erstellen?`)) return;
    showProgress('DROP ARCHITECTURE WIRD ERSTELLT...', 'ANALYSEN WERDEN DURCHSUCHT...');
    try {
        const resp = await fetch('/api/export/drop_architecture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, mode: state.exportMode }),
        });
        const data = await resp.json();
        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('DROP ARCHITECTURE FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function createTransitionMastery(duration) {
    if (!confirm(`Möchtest du eine ${duration}s lange Transition Mastery (ruhige Phase) erstellen?`)) return;
    showProgress('TRANSITION MASTERY WIRD ERSTELLT...', 'ANALYSEN WERDEN DURCHSUCHT...');
    try {
        const resp = await fetch('/api/export/transition_mastery', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration, mode: state.exportMode }),
        });
        const data = await resp.json();
        if (data.status === 'started' && data.job_id) {
            pollExportStatus(data.job_id, 1);
        } else {
            hideProgress();
            showToast(`FEHLER: ${data.error || 'UNBEKANNTER FEHLER'}`, 'error');
        }
    } catch (err) {
        hideProgress();
        showToast('TRANSITION MASTERY FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

async function resetUsageLog() {
    if (!confirm('ROTATION RESET: Alle "Featured"-Zähler werden auf 0 gesetzt. Videos werden danach wieder gleichwertig ausgewählt.')) return;
    try {
        const resp = await fetch('/api/reset_usage_log', { method: 'POST' });
        const data = await resp.json();
        if (data.status === 'success') {
            showToast('ROTATION RESET – ALLE VIDEOS GLEICHWERTIG', 'success');
            loadVideos();
        }
    } catch (err) {
        showToast('RESET FEHLGESCHLAGEN', 'error');
        console.error(err);
    }
}

// ============================================
// BPM TEMPO-MATCH
// ============================================
function onBpmToggle() {
    const on = dom.bpmMatchToggle.checked;
    dom.bpmSlider.disabled = !on;
    dom.bpmControl.classList.toggle('active', on);
    updateBpmLabel();
}

function updateBpmLabel() {
    dom.bpmValue.innerHTML = dom.bpmMatchToggle.checked
        ? `${dom.bpmSlider.value}<em>BPM</em>`
        : 'OFF';
}

// Aktuelle Ziel-BPM (oder null wenn Tempo-Match aus ist) – wird allen Export-Requests mitgegeben.
function getTargetBpm() {
    return dom.bpmMatchToggle.checked ? parseInt(dom.bpmSlider.value, 10) : null;
}

// ============================================
// FUNCTION INFO TOOLTIPS (Hover mit Verzögerung)
// ============================================
const TOOLTIP_DELAY = 500; // ms Verweildauer, bevor das Info-Popup erscheint

function initFunctionTooltips() {
    const tip = document.createElement('div');
    tip.id = 'funcTooltip';
    tip.innerHTML = '<div class="func-tooltip-title"></div><div class="func-tooltip-body"></div>';
    document.body.appendChild(tip);
    const tipTitle = tip.querySelector('.func-tooltip-title');
    const tipBody = tip.querySelector('.func-tooltip-body');

    let timer = null;
    const hide = () => {
        clearTimeout(timer);
        tip.classList.remove('visible');
        tip.style.left = '-9999px';
    };

    document.querySelectorAll('.command-row[data-info]').forEach(row => {
        row.addEventListener('mouseenter', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                const mark = row.querySelector('.command-cat-mark');
                tipTitle.textContent = row.querySelector('.command-name')?.textContent.trim() || 'INFO';
                tipBody.textContent = row.getAttribute('data-info') || '';
                tip.style.setProperty('--accent', mark ? getComputedStyle(mark).backgroundColor : '#ffffff');
                tip.classList.add('visible');
                positionTooltip(tip, row);
            }, TOOLTIP_DELAY);
        });
        row.addEventListener('mouseleave', hide);
    });

    // Beim Scrollen/Resize ausblenden, sonst klebt das Popup an der alten Stelle
    window.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
}

function positionTooltip(tip, row) {
    const r = row.getBoundingClientRect();
    const tw = tip.offsetWidth;
    const th = tip.offsetHeight;
    const margin = 10;

    // Bevorzugt oberhalb der Zeile, sonst darunter
    let top = r.top - th - margin;
    if (top < margin) top = r.bottom + margin;

    // Linksbündig zur Zeile, aber im Viewport halten
    let left = Math.min(r.left, window.innerWidth - tw - margin);
    if (left < margin) left = margin;

    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
}

function renderVideoCard(video) {
    const analyzedClass = video.is_analyzed ? 'analyzed' : '';
    const featuredClass = video.usage_count > 0 ? 'featured' : '';

    return `
        <div class="video-card ${analyzedClass} ${featuredClass}"
             onclick="openVideo('${escapeHtml(video.filename)}')"
             title="${escapeHtml(video.filename)}">
            <div class="video-thumb">
                ${video.has_thumbnail
                    ? `<img src="/api/thumbnail/${encodeURIComponent(video.filename)}" alt="${escapeHtml(video.filename)}" loading="lazy">`
                    : `<span class="placeholder-icon">🎬</span>`
                }
                <div class="play-overlay">
                    <div class="play-btn">▶</div>
                </div>
                ${video.usage_count > 0 ? `<div class="usage-badge">✨ FEATURED ${video.usage_count}X</div>` : ''}
            </div>
            <div class="video-info">
                <div class="video-name">${escapeHtml(video.filename)}</div>
                <div class="video-meta">
                    <span>${video.size_mb} MB</span>
                    ${video.is_analyzed ? '<span style="color: var(--acid-green)">// READY</span>' : '<span style="color: var(--muted-grey)">// PROCESSING...</span>'}
                </div>
            </div>
        </div>
    `;
}

function renderVideoGrid() {
    if (state.videos.length === 0) {
        dom.videoGrid.style.display = 'none';
        dom.emptyLibrary.style.display = 'block';
        return;
    }

    dom.videoGrid.style.display = 'grid';
    dom.emptyLibrary.style.display = 'none';

    dom.videoGrid.innerHTML = state.videos.map(renderVideoCard).join('');
}

// ============================================
// OPEN VIDEO / PRODUCTION VIEW
// ============================================
async function openVideo(filename) {
    state.currentVideo = filename;
    state.analysisResults = null;
    state.selectedClips.clear();
    state.suggestedClips = [];

    // Update UI
    dom.analysisVideoName.textContent = filename.toUpperCase();
    dom.videoSource.src = `/api/video/${encodeURIComponent(filename)}`;
    dom.videoPlayer.load();

    // Reset watermark bar
    state.wmResult = null;
    dom.wmResult.textContent = 'CAPCUT WATERMARK CHECK';
    dom.wmResult.className = 'wm-result';
    dom.wmRemoveBtn.style.visibility = 'hidden';
    dom.wmScanBtn.textContent = 'WM SCAN';
    dom.wmScanBtn.disabled = false;

    // Hide analysis panels initially
    dom.statsRow.style.display = 'none';
    dom.timelineSection.style.display = 'none';
    dom.clipsPanel.style.display = 'none';

    // Switch to analysis view
    switchView('analysis');

    // 1. Check if results already exist
    try {
        const resp = await fetch(`/api/results/${encodeURIComponent(filename)}`);
        if (resp.ok) {
            const results = await resp.json();
            if (!results.error) {
                state.analysisResults = results;
                displayResults(results);
                return;
            }
        }
    } catch (err) {}

    // 2. Start analysis actively since we want to view it now
    try {
        const startResp = await fetch(`/api/analyze/${encodeURIComponent(filename)}`, { method: 'POST' });
        const startData = await startResp.json();
        // If it was already running or just started, poll for it but SHOW the overlay
        pollAnalysisStatus(filename, false);
    } catch (err) {
        console.error("Failed to start analysis", err);
    }
}

// ============================================
// ANALYSIS POLLING
// ============================================
function pollAnalysisStatus(filename, silent = false) {
    if (state.pollInterval) clearInterval(state.pollInterval);

    state.pollInterval = setInterval(async () => {
        try {
            const resp = await fetch(`/api/status/${encodeURIComponent(filename)}`);
            const status = await resp.json();

            if (status.status === 'running') {
                if (!silent) {
                    showProgress('VIDEO WIRD ANALYSIERT...', `FORTSCHRITT: ${status.progress}%`);
                    updateProgress(status.progress, status.message);
                } else {
                    // Falls wir in der PRODUKTION Ansicht sind und auf das Video warten
                    dom.analysisVideoName.textContent = `${filename.toUpperCase()} (ANALYSING ${status.progress}%)`;
                }
            }

            if (status.status === 'completed') {
                clearInterval(state.pollInterval);
                state.pollInterval = null;
                if (!silent) hideProgress();
                
                showToast('ANALYSE ABGESCHLOSSEN! 🎉', 'success');
                
                // Erneut versuchen die Ergebnisse zu laden
                const resResp = await fetch(`/api/results/${encodeURIComponent(filename)}`);
                if (resResp.ok) {
                    const results = await resResp.json();
                    state.analysisResults = results;
                    displayResults(results);
                }
            } else if (status.status === 'error') {
                clearInterval(state.pollInterval);
                state.pollInterval = null;
                if (!silent) hideProgress();
                showToast(`FEHLER BEI DER ANALYSE: ${status.message}`, 'error');
            }
        } catch (err) {
            console.error('Analyse-Poll Fehler:', err);
        }
    }, 2000);
}

// ============================================
// DISPLAY RESULTS
// ============================================
function displayResults(results) {
    // Stats
    dom.statsRow.style.display = 'grid';
    dom.statTempo.textContent = Math.round(results.audio?.tempo || 0);
    dom.statDuration.textContent = formatDuration(results.audio?.duration || 0);
    dom.statHighlights.textContent = results.highlights?.length || 0;
    dom.statDrops.textContent = results.audio?.bass_drops?.length || 0;
    dom.statClips.textContent = results.suggested_clips?.length || 0;

    // Timeline
    dom.timelineSection.style.display = 'block';
    drawTimeline(results);

    // Time labels
    const duration = results.audio?.duration || 0;
    dom.timeStart.textContent = '0:00';
    dom.timeMid.textContent = formatDuration(duration / 2);
    dom.timeEnd.textContent = formatDuration(duration);

    // Clips
    state.suggestedClips = results.suggested_clips || [];
    dom.clipsPanel.style.display = 'flex';
    dom.clipCountBadge.textContent = state.suggestedClips.length;
    renderClipsList();
}

// ============================================
// TIMELINE CANVAS
// ============================================
function drawTimeline(results) {
    const canvas = dom.timelineCanvas;
    const wrapper = dom.timelineWrapper;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = wrapper.clientWidth * dpr;
    canvas.height = wrapper.clientHeight * dpr;
    canvas.style.width = wrapper.clientWidth + 'px';
    canvas.style.height = wrapper.clientHeight + 'px';

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight;
    const timeline = results.timeline || [];
    if (timeline.length === 0) return;

    const duration = results.audio?.duration || timeline[timeline.length - 1].time;

    // Background
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = '#1c1c1c';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
        const x = (i / 10) * w;
        ctx.beginPath();
        ctx.moveTo(x, 0); ctx.lineTo(x, h);
        ctx.stroke();
    }

    // Highlight regions
    const highlights = results.highlights || [];
    highlights.forEach(hl => {
        const x1 = (hl.start / duration) * w;
        const x2 = (hl.end / duration) * w;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.fillRect(x1, 0, x2 - x1, h);
    });

    // Draw channels
    const channels = [
        { key: 'audio_energy', color: '#00f2ff', alpha: 0.8 },
        { key: 'bass_drops',   color: '#ff00e5', alpha: 0.6 },
        { key: 'motion',       color: '#ccff00', alpha: 0.6 },
    ];

    channels.forEach(ch => {
        ctx.beginPath();
        ctx.strokeStyle = ch.color;
        ctx.lineWidth = 1;
        ctx.globalAlpha = ch.alpha;

        const baseY = h * 0.95;
        timeline.forEach((point, i) => {
            const x = (point.time / duration) * w;
            const val = point.components?.[ch.key] || 0;
            const y = baseY - val * h * 0.9;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    });

    // Overall score
    ctx.beginPath();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.globalAlpha = 1;
    const baseY = h * 0.95;
    timeline.forEach((point, i) => {
        const x = (point.time / duration) * w;
        const y = baseY - (point.score || 0) * h * 0.9;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
}

// ============================================
// PLAYHEAD
// ============================================
function updatePlayhead() {
    if (!state.analysisResults) return;
    const duration = dom.videoPlayer.duration || 1;
    const currentTime = dom.videoPlayer.currentTime;
    const pct = (currentTime / duration) * 100;
    dom.playhead.style.left = `${pct}%`;
}

// ============================================
// CLIPS LIST
// ============================================
function getQualityTier(score) {
    if (score >= 0.90) return { label: 'ELITE (S)', class: 'tier-s', color: '#00f2ff' };
    if (score >= 0.75) return { label: 'GOLD (A)', class: 'tier-a', color: '#ffffff' };
    if (score >= 0.50) return { label: 'GREAT (B)', class: 'tier-b', color: '#333333' };
    return { label: 'GOOD (C)', class: 'tier-c', color: '#1c1c1c' };
}

function renderClipsList() {
    let clips = state.suggestedClips;
    if (state.currentPresetFilter !== 'all') {
        clips = clips.filter(c => c.preset === state.currentPresetFilter);
    }

    // Sort by score descending (highest rated first)
    clips.sort((a, b) => b.score - a.score);

    if (clips.length === 0) {
        dom.clipsList.innerHTML = `<div class="empty-state"><p>// NO CLIPS FOUND</p></div>`;
        return;
    }

    dom.clipsList.innerHTML = clips.map((clip, idx) => {
        const scorePercent = Math.round(clip.score * 100);
        const isSelected = state.selectedClips.has(clipId(clip));
        const tier = getQualityTier(clip.score);

        return `
            <div class="clip-card ${isSelected ? 'selected' : ''}"
                 onclick="toggleClipSelection('${clipId(clip)}')"
                 data-clip-id="${clipId(clip)}">
                <div class="clip-tier-badge ${tier.class}">${tier.label}</div>
                <div class="clip-details">
                    <div class="clip-time">${formatTime(clip.start)} – ${formatTime(clip.end)}</div>
                    <div class="clip-duration-tag">${clip.preset_label.toUpperCase()} · ${clip.duration}S · SCORE: ${scorePercent}</div>
                </div>
                <div class="clip-actions">
                    <button class="clip-action-btn" onclick="event.stopPropagation(); previewClip(${clip.start}, ${clip.end})" title="PREVIEW">▶</button>
                    ${clip.duration >= 2 ? `<button class="clip-action-btn" onclick="event.stopPropagation(); exportSingleLoopClip(${clip.start}, ${clip.end})" title="SEAMLESS LOOP EXPORT">♾️</button>` : ''}
                    <button class="clip-action-btn" onclick="event.stopPropagation(); exportSingleClip(${clip.start}, ${clip.end})" title="EXPORT">📤</button>
                </div>
            </div>
        `;
    }).join('');
}

function clipId(clip) {
    return `${clip.start}-${clip.end}-${clip.preset}`;
}

function toggleClipSelection(id) {
    if (state.selectedClips.has(id)) {
        state.selectedClips.delete(id);
    } else {
        state.selectedClips.add(id);
    }
    renderClipsList();
}

function autoSelectTransitionReel(targetDuration) {
    if (state.suggestedClips.length === 0) return;
    state.selectedClips.clear();
    let pool = state.suggestedClips.filter(c => c.duration <= 3);
    pool.sort((a, b) => b.score - a.score);
    let selected = [];
    let currentTotal = 0;

    for (const clip of pool) {
        if (currentTotal >= targetDuration - 0.5) break;

        const wouldTotal = currentTotal + clip.duration;
        const remaining  = targetDuration - currentTotal;

        // Clip überspringen wenn:
        // a) er zu stark überschießt (>+1s) UND die verbleibende Lücke
        //    kleiner als halbe Clip-Dauer ist (Clip würde kaum was füllen)
        if (wouldTotal > targetDuration + 1 && remaining < clip.duration * 0.5) continue;
        // Hartes Limit: nie mehr als eine volle Clip-Länge über das Ziel
        if (wouldTotal > targetDuration + clip.duration) continue;

        const overlaps = selected.some(s => clip.start < s.end && clip.end > s.start);
        if (!overlaps) {
            selected.push(clip);
            currentTotal += clip.duration;
            state.selectedClips.add(clipId(clip));
        }
    }

    renderClipsList();
    showToast(`${selected.length} CLIPS SELECTED (${currentTotal.toFixed(1)}s)`, 'success');
}

// ============================================
// PREVIEW
// ============================================
function previewClip(start, end) {
    dom.videoPlayer.currentTime = start;
    dom.videoPlayer.play();
    const checkEnd = () => {
        if (dom.videoPlayer.currentTime >= end) {
            dom.videoPlayer.pause();
            dom.videoPlayer.removeEventListener('timeupdate', checkEnd);
        }
    };
    dom.videoPlayer.addEventListener('timeupdate', checkEnd);
}

// ============================================
// EXPORT
// ============================================
function setExportMode(mode) {
    state.exportMode = mode;
    dom.exportModeReel.classList.toggle('active', mode === 'reel');
    dom.exportModeRaw.classList.toggle('active', mode === 'raw');
}

async function exportSingleClip(start, end) {
    if (!state.currentVideo) return;
    showToast('EXPORT STARTED', 'info');
    try {
        const resp = await fetch('/api/export/single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: state.currentVideo, start: start, end: end,
                mode: state.exportMode, fade: dom.fadeToggle.checked,
                target_bpm: getTargetBpm(),
            })
        });
        const data = await resp.json();
        if (data.status === 'success') {
            showToast('CLIP EXPORTED', 'success');
            // Auto-download
            if (data.export && data.export.filename) {
                // Die API speichert nun alle normalen Clips unter single_downloads
                const fileUrl = `/api/output/single_downloads/${encodeURIComponent(data.export.filename)}`;
                const a = document.createElement('a');
                a.href = fileUrl;
                a.download = data.export.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
        }
    } catch (err) { console.error(err); }
}

async function exportSingleLoopClip(start, end) {
    if (!state.currentVideo) return;
    showToast('LOOP EXPORT STARTED', 'info');
    try {
        const resp = await fetch('/api/export/single_loop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: state.currentVideo, start: start, end: end,
                mode: state.exportMode,
                target_bpm: getTargetBpm()
            })
        });
        const data = await resp.json();
        if (data.status === 'success') {
            showToast('LOOP EXPORTED', 'success');
            // Auto-download
            if (data.export && data.export.filename) {
                const fileUrl = `/api/output/single_downloads/${encodeURIComponent(data.export.filename)}`;
                const a = document.createElement('a');
                a.href = fileUrl;
                a.download = data.export.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
        } else {
            showToast(`ERROR: ${data.error}`, 'error');
        }
    } catch (err) { console.error(err); }
}

async function exportSelected() {
    const clips = state.suggestedClips.filter(c => state.selectedClips.has(clipId(c)));
    if (clips.length > 0) await batchExport(clips);
}

async function exportAll() {
    let clips = state.suggestedClips;
    if (state.currentPresetFilter !== 'all') {
        clips = clips.filter(c => c.preset === state.currentPresetFilter);
    }
    if (clips.length > 0) await batchExport(clips);
}

async function batchExport(clips) {
    if (!state.currentVideo) return;
    showProgress('BATCH EXPORT...', `${clips.length} CLIPS IN QUEUE...`);
    try {
        const resp = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: state.currentVideo,
                clips: clips.map(c => ({ start: c.start, end: c.end })),
                mode: state.exportMode, fade: dom.fadeToggle.checked,
                target_bpm: getTargetBpm(),
            })
        });
        const data = await resp.json();
        if (data.job_id) pollExportStatus(data.job_id, clips.length);
    } catch (err) { hideProgress(); console.error(err); }
}

function pollExportStatus(jobId, totalClips) {
    // Job-ID merken + Cancel-Button zeigen
    state.activeExportJobId = jobId;
    dom.progressCancelBtn.style.display = 'block';

    const interval = setInterval(async () => {
        try {
            const resp = await fetch(`/api/export/status/${encodeURIComponent(jobId)}`);
            const status = await resp.json();
            updateProgress(status.progress || 0, status.message?.toUpperCase());

            if (status.status === 'completed') {
                clearInterval(interval);
                hideProgress();
                showToast('EXPORT COMPLETE', 'success');
            } else if (status.status === 'cancelled') {
                clearInterval(interval);
                hideProgress();
                showToast('EXPORT ABGEBROCHEN', 'info');
            } else if (status.status === 'error') {
                clearInterval(interval);
                hideProgress();
                showToast('EXPORT FAILED', 'error');
            }
        } catch (err) { console.error(err); }
    }, 1500);
}

async function cancelCurrentExport() {
    const jobId = state.activeExportJobId;
    if (!jobId) return;

    if (!confirm(
        'EXPORT ABBRECHEN?\n\n' +
        'Das unfertige Datenfragment wird unwiderruflich gelöscht.\n' +
        'Dieser Vorgang kann nicht rückgängig gemacht werden.'
    )) return;

    try {
        const resp = await fetch(`/api/export/cancel/${encodeURIComponent(jobId)}`, {
            method: 'POST',
        });
        const data = await resp.json();
        hideProgress();
        const msg = data.file_deleted
            ? 'ABGEBROCHEN – FRAGMENT GELÖSCHT'
            : 'ABGEBROCHEN';
        showToast(msg, 'info');
    } catch (err) {
        hideProgress();
        console.error('Cancel fehlgeschlagen:', err);
    }
}


// ============================================
// WATERMARK DETECTION & REMOVAL
// ============================================
async function runWatermarkScan() {
    if (!state.currentVideo) return;
    dom.wmScanBtn.textContent = 'SCANNING...';
    dom.wmScanBtn.disabled = true;
    dom.wmResult.textContent = '...';
    dom.wmResult.className = 'wm-result';
    dom.wmRemoveBtn.style.visibility = 'hidden';

    try {
        const resp = await fetch(`/api/watermark/detect/${encodeURIComponent(state.currentVideo)}`, {
            method: 'POST'
        });
        const data = await resp.json();
        state.wmResult = data;

        if (data.error) {
            dom.wmResult.textContent = `ERROR: ${data.error}`;
        } else if (data.detected) {
            let msg = 'WATERMARK DETECTED:';
            if (data.trim_start > 0) msg += `  START +${data.trim_start}s`;
            if (data.trim_end   > 0) msg += `  END -${data.trim_end}s`;
            dom.wmResult.textContent = msg;
            dom.wmResult.className = 'wm-result wm-result--found';
            dom.wmRemoveBtn.style.visibility = 'visible';
        } else {
            dom.wmResult.textContent = 'NO WATERMARK DETECTED';
            dom.wmResult.className = 'wm-result wm-result--clean';
        }
    } catch (err) {
        dom.wmResult.textContent = 'SCAN ERROR';
        console.error(err);
    } finally {
        dom.wmScanBtn.textContent = 'WM SCAN';
        dom.wmScanBtn.disabled = false;
    }
}

async function removeWatermark() {
    const d = state.wmResult;
    if (!d || !d.detected) return;
    showProgress('WATERMARK REMOVAL...', 'TRIMMING VIDEO...');
    try {
        const resp = await fetch(`/api/watermark/remove/${encodeURIComponent(state.currentVideo)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                trim_start: d.trim_start,
                trim_end:   d.trim_end,
                duration:   d.duration,
            }),
        });
        const data = await resp.json();
        if (data.job_id) pollExportStatus(data.job_id, 1);
        else { hideProgress(); showToast('ERROR', 'error'); }
    } catch (err) {
        hideProgress();
        console.error(err);
    }
}

async function batchCleanWatermarks() {
    if (!confirm('Alle exportierten Clips auf CapCut Watermarks scannen und bereinigen?')) return;
    showProgress('WM CLEANUP RUNNING...', 'SCANNING EXPORTS...');
    try {
        const resp = await fetch('/api/watermark/batch_clean', { method: 'POST' });
        const data = await resp.json();
        if (data.job_id) pollExportStatus(data.job_id, 1);
        else { hideProgress(); showToast('ERROR', 'error'); }
    } catch (err) {
        hideProgress();
        console.error(err);
    }
}

// ============================================
// OVERLAYS
// ============================================
function showProgress(title, message) {
    dom.progressTitle.textContent = title.toUpperCase();
    dom.progressMessage.textContent = message.toUpperCase();
    dom.progressBarFill.style.width = '0%';
    dom.progressPercentage.textContent = '0%';
    dom.progressOverlay.classList.add('active');
}

function updateProgress(percent, message) {
    dom.progressBarFill.style.width = `${percent}%`;
    dom.progressPercentage.textContent = `${percent}%`;
    if (message) dom.progressMessage.textContent = message.toUpperCase();
}

function hideProgress() {
    dom.progressOverlay.classList.remove('active');
    dom.progressCancelBtn.style.display = 'none';
    state.activeExportJobId = null;
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>// ${escapeHtml(message.toUpperCase())}</span>`;
    dom.toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// UTILS
// ============================================
function formatDuration(s) {
    if (!s || isNaN(s)) return '0:00';
    return `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,'0')}`;
}
function formatTime(s) { return formatDuration(s); }
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

window.addEventListener('resize', () => {
    if (state.analysisResults) drawTimeline(state.analysisResults);
});
