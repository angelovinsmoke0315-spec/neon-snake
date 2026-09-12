from flask import Flask, jsonify, request, render_template_string
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
DB = Path(__file__).with_name("puntuaciones.db")


# =========================================================
# BASE DE DATOS
# =========================================================

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def columna_existe(conn, tabla, columna):
    columnas = conn.execute(f"PRAGMA table_info({tabla})").fetchall()
    return any(c["name"] == columna for c in columnas)


def init_db():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS puntuaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jugador TEXT NOT NULL DEFAULT 'Jugador',
                score INTEGER NOT NULL CHECK(score >= 0),
                dificultad TEXT NOT NULL DEFAULT 'Normal',
                fecha TEXT NOT NULL
            )
        """)

        # Migra automáticamente la BD vieja si ya existe.
        if not columna_existe(conn, "puntuaciones", "jugador"):
            conn.execute("""
                ALTER TABLE puntuaciones
                ADD COLUMN jugador TEXT NOT NULL DEFAULT 'Jugador'
            """)

        if not columna_existe(conn, "puntuaciones", "dificultad"):
            conn.execute("""
                ALTER TABLE puntuaciones
                ADD COLUMN dificultad TEXT NOT NULL DEFAULT 'Normal'
            """)

        conn.commit()


# =========================================================
# HTML + CSS + JAVASCRIPT
# =========================================================

HTML = r"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neon Snake Ultra</title>

<style>
:root{
    --cyan:#00f7ff;
    --cyan2:#00a8ff;
    --gold:#ffd84d;
    --pink:#ff2d75;
    --purple:#8d62ff;
    --green:#5dff9a;
    --panel:rgba(10,16,29,.90);
    --panel2:#0d1423;
    --muted:#7d89ac;
    --border:#22314f;
}

*{box-sizing:border-box}

html,body{
    margin:0;
    min-height:100%;
}

body{
    min-height:100vh;
    color:white;
    font-family:"Courier New",monospace;
    overflow-x:hidden;
    background:
        radial-gradient(circle at 20% 0%, rgba(0,247,255,.13), transparent 30%),
        radial-gradient(circle at 80% 10%, rgba(141,98,255,.16), transparent 30%),
        linear-gradient(180deg,#07101d,#03050a 70%);
}

body::before{
    content:"";
    position:fixed;
    inset:0;
    pointer-events:none;
    opacity:.25;
    background-image:
        linear-gradient(rgba(0,247,255,.05) 1px, transparent 1px),
        linear-gradient(90deg,rgba(0,247,255,.05) 1px, transparent 1px);
    background-size:32px 32px;
    mask-image:linear-gradient(to bottom,black,transparent 85%);
}

.page{
    width:min(1120px,96vw);
    margin:auto;
    padding:22px 0 40px;
}

header{
    text-align:center;
    margin-bottom:18px;
}

.logo{
    margin:0;
    font-size:clamp(30px,5vw,52px);
    letter-spacing:5px;
    color:var(--cyan);
    text-shadow:
        0 0 8px var(--cyan),
        0 0 20px rgba(0,247,255,.55),
        0 0 42px rgba(0,168,255,.24);
}

.logo span{color:white}

.subtitle{
    color:var(--muted);
    font-size:13px;
    margin-top:5px;
    letter-spacing:1px;
}

.layout{
    display:grid;
    grid-template-columns:minmax(0,520px) minmax(260px,1fr);
    gap:18px;
    align-items:start;
}

.panel{
    position:relative;
    background:linear-gradient(180deg,rgba(14,22,38,.94),rgba(6,11,20,.94));
    border:1px solid var(--border);
    border-radius:20px;
    box-shadow:
        0 20px 60px rgba(0,0,0,.38),
        inset 0 1px rgba(255,255,255,.03);
    padding:15px;
}

.panel::before{
    content:"";
    position:absolute;
    inset:0;
    border-radius:20px;
    pointer-events:none;
    border:1px solid rgba(0,247,255,.06);
}

.hud{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin-bottom:10px;
}

.stat{
    min-width:0;
    text-align:center;
    padding:9px 4px;
    border-radius:12px;
    background:linear-gradient(180deg,#0b1220,#080d17);
    border:1px solid #1e2b46;
}

.stat strong{
    display:block;
    font-size:20px;
    line-height:1.05;
    color:var(--cyan);
    overflow:hidden;
    text-overflow:ellipsis;
}

.stat small{
    display:block;
    margin-top:3px;
    color:#7885a9;
    font-size:10px;
    letter-spacing:.7px;
}

#record{color:var(--gold)}
#combo{color:var(--green)}
#level{color:#d3bcff}

.subhud{
    display:flex;
    flex-wrap:wrap;
    justify-content:center;
    align-items:center;
    gap:8px 16px;
    min-height:30px;
    color:#8592b5;
    font-size:12px;
    margin-bottom:7px;
}

.subhud .pill{
    padding:4px 9px;
    border:1px solid #263654;
    background:#0a101c;
    border-radius:999px;
}

.board-wrap{
    position:relative;
    width:440px;
    height:440px;
    max-width:100%;
    margin:auto;
}

canvas{
    display:block;
    width:100%;
    height:auto;
    background:#0d1420;
    border:3px solid var(--cyan);
    border-radius:18px;
    box-shadow:
        0 0 12px rgba(0,247,255,.7),
        0 0 35px rgba(0,168,255,.25),
        inset 0 0 35px rgba(0,0,0,.4);
}

.overlay{
    position:absolute;
    inset:0;
    display:grid;
    place-content:center;
    text-align:center;
    padding:28px;
    border-radius:18px;
    background:rgba(3,8,17,.88);
    backdrop-filter:blur(7px);
    z-index:5;
}

.hidden{display:none!important}

.menu-card{
    width:min(340px,90vw);
}

.menu-title{
    font-size:28px;
    font-weight:bold;
    color:var(--cyan);
    margin-bottom:12px;
    text-shadow:0 0 12px rgba(0,247,255,.5);
}

.field{
    text-align:left;
    margin:10px 0;
}

.field label{
    display:block;
    font-size:11px;
    color:#93a0bf;
    margin-bottom:5px;
}

input,select{
    width:100%;
    border:1px solid #304263;
    border-radius:10px;
    background:#08101d;
    color:white;
    padding:11px;
    font:inherit;
    outline:none;
}

input:focus,select:focus{
    border-color:var(--cyan);
    box-shadow:0 0 0 2px rgba(0,247,255,.08);
}

button{
    border:0;
    border-radius:10px;
    padding:11px 14px;
    cursor:pointer;
    font:inherit;
    font-weight:bold;
    transition:.16s ease;
}

button:hover{transform:translateY(-1px)}
button:active{transform:translateY(1px)}

.primary{
    background:linear-gradient(90deg,var(--cyan),#61fff0);
    color:#001014;
    box-shadow:0 0 18px rgba(0,247,255,.22);
}

.secondary{
    background:#18243a;
    color:white;
    border:1px solid #2d4165;
}

.danger{
    background:#3d1628;
    color:#ff9abb;
    border:1px solid #6a2443;
}

.menu-actions{
    display:flex;
    gap:8px;
    justify-content:center;
    flex-wrap:wrap;
    margin-top:10px;
}

.big-button{
    width:100%;
    margin-top:8px;
}

.final-title{
    font-size:27px;
    font-weight:bold;
    margin-bottom:10px;
}

.final-text{
    line-height:1.6;
    color:#d9dff3;
}

.help{
    text-align:center;
    color:#697694;
    font-size:11px;
    margin-top:9px;
    line-height:1.55;
}

.side h2{
    text-align:center;
    margin:2px 0 11px;
    color:var(--gold);
    text-shadow:0 0 12px rgba(255,216,77,.18);
}

#topList{
    margin:0;
    padding-left:28px;
    line-height:1.7;
}

#topList li{
    padding:5px 0;
    border-bottom:1px dashed #26314a;
}

#topList li::marker{
    color:var(--gold);
    font-weight:bold;
}

.row-score{
    display:flex;
    justify-content:space-between;
    gap:8px;
}

.badge{
    flex:none;
    font-size:10px;
    padding:1px 6px;
    border-radius:999px;
    color:#bac6e4;
    background:#18233a;
    border:1px solid #2a3b5d;
}

.legend{
    margin-top:14px;
    display:grid;
    gap:7px;
    font-size:12px;
    color:#9aa6c7;
}

.legend-row{
    display:flex;
    align-items:center;
    gap:8px;
}

.dot{
    width:12px;
    height:12px;
    border-radius:50%;
    display:inline-block;
    box-shadow:0 0 10px currentColor;
}

.red{background:#ff416c;color:#ff416c}
.gold{background:#ffd84d;color:#ffd84d}
.blue{background:#00f7ff;color:#00f7ff}
.purple{background:#8d62ff;color:#8d62ff}

.controls-box{
    margin-top:15px;
    padding-top:13px;
    border-top:1px solid #202c45;
}

.keys{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:7px;
    font-size:12px;
    color:#97a5c8;
}

.kbd{
    color:white;
    background:#141d30;
    border:1px solid #2a3a58;
    border-bottom-width:3px;
    padding:2px 7px;
    border-radius:6px;
}

.touch{
    display:none;
    grid-template-columns:repeat(3,58px);
    grid-template-rows:repeat(2,50px);
    gap:6px;
    justify-content:center;
    margin-top:12px;
}

.touch button{
    font-size:22px;
    padding:0;
    background:#142039;
    color:white;
    border:1px solid #2b4168;
}

.touch .up{grid-column:2}
.touch .left{grid-column:1;grid-row:2}
.touch .down{grid-column:2;grid-row:2}
.touch .right{grid-column:3;grid-row:2}

.toast{
    position:fixed;
    left:50%;
    bottom:24px;
    transform:translateX(-50%) translateY(20px);
    opacity:0;
    pointer-events:none;
    background:#0c1424;
    border:1px solid #2b4168;
    color:white;
    border-radius:10px;
    padding:10px 14px;
    transition:.2s ease;
    z-index:20;
    box-shadow:0 10px 30px rgba(0,0,0,.35);
}

.toast.show{
    opacity:1;
    transform:translateX(-50%) translateY(0);
}

@media(max-width:850px){
    .layout{grid-template-columns:1fr}
    .side{width:min(520px,100%);margin:auto}
}

@media(max-width:560px){
    .hud{grid-template-columns:repeat(2,1fr)}
    .board-wrap{width:min(440px,92vw);height:auto;aspect-ratio:1}
    .touch{display:grid}
    .keys{grid-template-columns:1fr}
}
</style>
</head>

<body>
<div class="page">
<header>
    <h1 class="logo">NEON <span>SNAKE</span> ULTRA</h1>
    <div class="subtitle">FLASK · SQLITE · CANVAS · ARCADE MODE</div>
</header>

<div class="layout">

<section class="panel">
    <div class="hud">
        <div class="stat">
            <strong id="score">0</strong>
            <small>SCORE</small>
        </div>

        <div class="stat">
            <strong id="record">0</strong>
            <small>HI-SCORE</small>
        </div>

        <div class="stat">
            <strong id="level">1</strong>
            <small>NIVEL</small>
        </div>

        <div class="stat">
            <strong id="combo">x1</strong>
            <small>COMBO</small>
        </div>
    </div>

    <div class="subhud">
        <span class="pill">⚡ <span id="speed">100%</span></span>
        <span class="pill">🎮 <span id="playerText">Jugador</span></span>
        <span class="pill" id="soundText">🔊 SONIDO</span>
    </div>

    <div class="board-wrap">
        <canvas id="game" width="440" height="440"></canvas>

        <div id="menuOverlay" class="overlay">
            <div class="menu-card">
                <div class="menu-title">🐍 NUEVA PARTIDA</div>

                <div class="field">
                    <label>NOMBRE DEL JUGADOR</label>
                    <input
                        id="playerName"
                        maxlength="20"
                        value="Angel"
                        autocomplete="off"
                    >
                </div>

                <div class="field">
                    <label>DIFICULTAD</label>
                    <select id="difficulty">
                        <option value="Facil">Fácil</option>
                        <option value="Normal" selected>Normal</option>
                        <option value="Dificil">Difícil</option>
                    </select>
                </div>

                <button id="startBtn" class="primary big-button">
                    ▶ COMENZAR
                </button>

                <div class="help">
                    El botón COMENZAR también activa el audio del navegador.
                </div>
            </div>
        </div>

        <div id="pauseOverlay" class="overlay hidden">
            <div>
                <div class="final-title" style="color:#ffd84d">
                    ⏸ PAUSA
                </div>

                <div class="final-text">
                    Presiona <b>P</b> o el botón para continuar.
                </div>

                <div class="menu-actions">
                    <button id="resumeBtn" class="primary">
                        CONTINUAR
                    </button>
                </div>
            </div>
        </div>

        <div id="endOverlay" class="overlay hidden">
            <div>
                <div id="finalTitle" class="final-title"></div>
                <div id="finalText" class="final-text"></div>

                <div class="menu-actions">
                    <button id="restartBtn" class="primary">
                        JUGAR OTRA VEZ
                    </button>

                    <button id="menuBtn" class="secondary">
                        MENÚ
                    </button>
                </div>
            </div>
        </div>
    </div>

    <div class="menu-actions">
        <button id="pauseBtn" class="secondary">⏸ PAUSA</button>
        <button id="soundBtn" class="secondary">🔊 SONIDO</button>
    </div>

    <div class="touch">
        <button class="up" data-dir="UP">▲</button>
        <button class="left" data-dir="LEFT">◀</button>
        <button class="down" data-dir="DOWN">▼</button>
        <button class="right" data-dir="RIGHT">▶</button>
    </div>

    <div class="help">
        Flechas o WASD para moverte · P pausa · M sonido · ESPACIO reinicia
    </div>
</section>


<aside class="panel side">
    <h2>🏆 TOP 10</h2>
    <ol id="topList"></ol>

    <div class="legend">
        <div class="legend-row">
            <span class="dot red"></span>
            Manzana normal: 10 pts
        </div>

        <div class="legend-row">
            <span class="dot gold"></span>
            Manzana dorada: 30 pts
            <b>(garantizada cada 5 comidas)</b>
        </div>

        <div class="legend-row">
            <span class="dot purple"></span>
            Obstáculo: aparece desde nivel 3
        </div>

        <div class="legend-row">
            <span class="dot blue"></span>
            Combo: come otra fruta antes de 4 s
        </div>
    </div>

    <div class="controls-box">
        <div class="keys">
            <div><span class="kbd">WASD</span> movimiento</div>
            <div><span class="kbd">↑↓←→</span> movimiento</div>
            <div><span class="kbd">P</span> pausa</div>
            <div><span class="kbd">M</span> silenciar</div>
            <div><span class="kbd">ESPACIO</span> reiniciar</div>
            <div><span class="kbd">ESC</span> menú</div>
        </div>
    </div>
</aside>

</div>
</div>

<div id="toast" class="toast"></div>


<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const scoreEl = document.getElementById("score");
const recordEl = document.getElementById("record");
const levelEl = document.getElementById("level");
const comboEl = document.getElementById("combo");
const speedEl = document.getElementById("speed");
const playerText = document.getElementById("playerText");
const soundText = document.getElementById("soundText");

const topList = document.getElementById("topList");
const toastEl = document.getElementById("toast");

const menuOverlay = document.getElementById("menuOverlay");
const pauseOverlay = document.getElementById("pauseOverlay");
const endOverlay = document.getElementById("endOverlay");

const finalTitle = document.getElementById("finalTitle");
const finalText = document.getElementById("finalText");

const playerNameInput = document.getElementById("playerName");
const difficultySelect = document.getElementById("difficulty");

const startBtn = document.getElementById("startBtn");
const restartBtn = document.getElementById("restartBtn");
const menuBtn = document.getElementById("menuBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resumeBtn = document.getElementById("resumeBtn");
const soundBtn = document.getElementById("soundBtn");


const CELL = 20;
const W = 440;
const H = 440;
const COLS = W / CELL;
const ROWS = H / CELL;
const TOTAL = COLS * ROWS;

const DIFFICULTIES = {
    Facil: 175,
    Normal: 140,
    Dificil: 105
};


let snake = [];
let direction = "RIGHT";
let nextDirection = "RIGHT";

let food = null;
let obstacles = [];
let particles = [];

let score = 0;
let record = 0;
let level = 1;
let combo = 1;

let player = "Jugador";
let difficulty = "Normal";

let playing = false;
let paused = false;
let saved = false;
let soundOn = true;

let timer = null;
let lastFoodAt = 0;
let foodsEaten = 0;
let goldenCountdown = 5;

let audioCtx = null;


// =========================================================
// UTILIDADES
// =========================================================

function toast(text){
    toastEl.textContent = text;
    toastEl.classList.add("show");

    clearTimeout(toastEl._timer);

    toastEl._timer = setTimeout(()=>{
        toastEl.classList.remove("show");
    },1800);
}


function escapeHtml(text){
    return String(text)
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}


// =========================================================
// AUDIO - WEB AUDIO API
// =========================================================

async function ensureAudio(){
    if(!audioCtx){
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }

    if(audioCtx.state === "suspended"){
        await audioCtx.resume();
    }
}


async function tone(
    frequency=440,
    duration=.07,
    type="sine",
    volume=.05,
    delay=0
){
    if(!soundOn) return;

    try{
        await ensureAudio();

        const start = audioCtx.currentTime + delay;
        const end = start + duration;

        const oscillator = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        oscillator.type = type;
        oscillator.frequency.setValueAtTime(frequency,start);

        gain.gain.setValueAtTime(volume,start);
        gain.gain.exponentialRampToValueAtTime(.0001,end);

        oscillator.connect(gain);
        gain.connect(audioCtx.destination);

        oscillator.start(start);
        oscillator.stop(end);
    }catch(error){
        console.warn("Audio no disponible:",error);
    }
}


function soundFood(){
    tone(520,.055,"square",.035);
    tone(660,.06,"square",.025,.045);
}


function soundGold(){
    tone(740,.08,"triangle",.045);
    tone(988,.10,"triangle",.045,.07);
    tone(1318,.13,"triangle",.035,.15);
}


function soundLevel(){
    tone(523,.08,"square",.03);
    tone(659,.08,"square",.03,.08);
    tone(784,.10,"square",.03,.16);
}


function soundDeath(){
    tone(220,.13,"sawtooth",.05);
    tone(165,.18,"sawtooth",.045,.11);
    tone(110,.25,"sawtooth",.04,.24);
}


function soundRecord(){
    tone(523,.10,"square",.03);
    tone(659,.10,"square",.03,.09);
    tone(784,.10,"square",.03,.18);
    tone(1046,.20,"triangle",.04,.28);
}


function soundPause(){
    tone(330,.06,"sine",.025);
}


function updateSoundUI(){
    soundBtn.textContent = soundOn ? "🔊 SONIDO" : "🔇 SILENCIO";
    soundText.textContent = soundOn ? "🔊 SONIDO" : "🔇 SILENCIO";
}


// =========================================================
// API DE PUNTUACIONES
// =========================================================

async function loadScores(){
    try{
        const response = await fetch("/api/scores");
        const data = await response.json();

        record = data.record || 0;
        recordEl.textContent = record;

        topList.innerHTML = "";

        if(data.top.length === 0){
            const li = document.createElement("li");
            li.textContent = "Aún no hay puntuaciones";
            topList.appendChild(li);
            return;
        }

        data.top.forEach(row=>{
            const li = document.createElement("li");

            li.innerHTML = `
                <div class="row-score">
                    <span>
                        <b>${escapeHtml(row.jugador)}</b>
                        · ${row.score}
                    </span>
                    <span class="badge">
                        ${escapeHtml(row.dificultad)}
                    </span>
                </div>
            `;

            li.title = row.fecha;
            topList.appendChild(li);
        });

    }catch(error){
        console.error("No se pudieron cargar puntuaciones:",error);
    }
}


async function saveScore(){
    if(saved) return;

    saved = true;

    try{
        const response = await fetch("/api/scores",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                jugador:player,
                score:score,
                dificultad:difficulty
            })
        });

        if(!response.ok){
            console.error("Puntuación rechazada por el servidor");
            return;
        }

        await loadScores();

    }catch(error){
        console.error("No se pudo guardar la puntuación:",error);
    }
}


// =========================================================
// JUEGO
// =========================================================

function startGame(){
    ensureAudio();

    player = playerNameInput.value.trim().slice(0,20) || "Jugador";
    difficulty = difficultySelect.value;

    playerText.textContent = `${player} · ${difficulty}`;

    snake = [
        {x:220,y:220},
        {x:200,y:220},
        {x:180,y:220}
    ];

    direction = "RIGHT";
    nextDirection = "RIGHT";

    food = null;
    obstacles = [];
    particles = [];

    score = 0;
    level = 1;
    combo = 1;

    foodsEaten = 0;
    goldenCountdown = 5;

    lastFoodAt = 0;

    playing = true;
    paused = false;
    saved = false;

    scoreEl.textContent = "0";
    levelEl.textContent = "1";
    comboEl.textContent = "x1";

    menuOverlay.classList.add("hidden");
    pauseOverlay.classList.add("hidden");
    endOverlay.classList.add("hidden");

    spawnFood();

    if(timer){
        clearTimeout(timer);
    }

    toast("¡Partida iniciada!");
    loop();
}


function restartGame(){
    startGame();
}


function goMenu(){
    playing = false;
    paused = false;

    if(timer){
        clearTimeout(timer);
    }

    pauseOverlay.classList.add("hidden");
    endOverlay.classList.add("hidden");
    menuOverlay.classList.remove("hidden");

    draw();
}


function randomCell(){
    return {
        x:Math.floor(Math.random()*COLS)*CELL,
        y:Math.floor(Math.random()*ROWS)*CELL
    };
}


function cellIsFree(pos){
    const snakeHit = snake.some(
        s=>s.x===pos.x && s.y===pos.y
    );

    const obstacleHit = obstacles.some(
        o=>o.x===pos.x && o.y===pos.y
    );

    const foodHit = (
        food &&
        food.x===pos.x &&
        food.y===pos.y
    );

    return !snakeHit && !obstacleHit && !foodHit;
}


function spawnFood(){
    if(snake.length + obstacles.length >= TOTAL-1){
        endGame(true);
        return;
    }

    for(let attempt=0;attempt<1200;attempt++){
        const pos = randomCell();

        if(!cellIsFree(pos)){
            continue;
        }

        /*
         * GARANTÍA DE MANZANA DORADA:
         * - Cada quinta comida será dorada.
         * - No depende únicamente de suerte.
         */
        const gold = goldenCountdown <= 1;

        food = {
            ...pos,
            type: gold ? "gold" : "normal"
        };

        if(gold){
            toast("⭐ ¡Apareció una manzana dorada!");
        }

        return;
    }

    endGame(true);
}


function updateLevel(){
    const newLevel = Math.floor(score/75)+1;

    if(newLevel <= level){
        return;
    }

    level = newLevel;
    levelEl.textContent = level;

    soundLevel();
    toast(`⚡ NIVEL ${level}`);

    if(level >= 3 && obstacles.length < 16){
        addObstacle();
    }

    if(level >= 5 && obstacles.length < 16){
        addObstacle();
    }
}


function addObstacle(){
    for(let attempt=0;attempt<500;attempt++){
        const pos = randomCell();
        const head = snake[0];

        const distance =
            Math.abs(pos.x-head.x)/CELL +
            Math.abs(pos.y-head.y)/CELL;

        if(cellIsFree(pos) && distance>5){
            obstacles.push(pos);
            return;
        }
    }
}


function burst(
    x,
    y,
    count=16,
    big=false,
    colors=null
){
    const palette = colors || [
        "#00f7ff",
        "#5dff9a",
        "#ffd84d",
        "#ff2d75",
        "#ffffff",
        "#8d62ff"
    ];

    for(let i=0;i<count;i++){
        const angle = Math.random()*Math.PI*2;
        const velocity =
            (big?2:1)+
            Math.random()*(big?7:5);

        particles.push({
            x:x,
            y:y,
            vx:Math.cos(angle)*velocity,
            vy:Math.sin(angle)*velocity,
            life:big?1.5:1,
            color:palette[
                Math.floor(Math.random()*palette.length)
            ],
            radius:2+Math.random()*3
        });
    }
}


function updateParticles(){
    particles = particles.filter(p=>{
        p.x += p.vx;
        p.y += p.vy;

        p.vx *= .985;
        p.vy += .035;

        p.life -= playing ? .095 : .022;

        return p.life>0;
    });
}


function eatFood(){
    const now = performance.now();

    if(lastFoodAt && now-lastFoodAt<=4000){
        combo = Math.min(combo+1,5);
    }else{
        combo = 1;
    }

    lastFoodAt = now;
    comboEl.textContent = `x${combo}`;

    const wasGold = food.type==="gold";

    let basePoints;

    if(wasGold){
        basePoints = 30;

        soundGold();

        burst(
            food.x+CELL/2,
            food.y+CELL/2,
            42,
            true,
            [
                "#ffd84d",
                "#fff7ae",
                "#ffffff",
                "#ffae00"
            ]
        );

        goldenCountdown = 5;
        toast(`⭐ +${basePoints*combo} PUNTOS`);

    }else{
        basePoints = 10;

        soundFood();

        burst(
            food.x+CELL/2,
            food.y+CELL/2,
            15,
            false,
            [
                "#ff416c",
                "#ff2d75",
                "#ff7043",
                "#ffd0dc"
            ]
        );

        goldenCountdown -= 1;
    }

    foodsEaten += 1;

    score += basePoints*combo;
    scoreEl.textContent = score;

    updateLevel();
    spawnFood();
}


function update(){
    updateParticles();

    if(!playing || paused){
        return;
    }

    if(
        lastFoodAt &&
        performance.now()-lastFoodAt>4000 &&
        combo!==1
    ){
        combo = 1;
        comboEl.textContent = "x1";
    }

    direction = nextDirection;

    const head = {...snake[0]};

    if(direction==="RIGHT"){
        head.x += CELL;
    }else if(direction==="LEFT"){
        head.x -= CELL;
    }else if(direction==="UP"){
        head.y -= CELL;
    }else if(direction==="DOWN"){
        head.y += CELL;
    }

    const wallHit =
        head.x<0 ||
        head.x>=W ||
        head.y<0 ||
        head.y>=H;

    const selfHit = snake.some(
        s=>s.x===head.x && s.y===head.y
    );

    const obstacleHit = obstacles.some(
        o=>o.x===head.x && o.y===head.y
    );

    if(wallHit || selfHit || obstacleHit){
        soundDeath();
        endGame(false);
        return;
    }

    snake.unshift(head);

    if(
        food &&
        head.x===food.x &&
        head.y===food.y
    ){
        eatFood();
    }else{
        snake.pop();
    }
}


async function endGame(victory){
    if(!playing){
        return;
    }

    playing = false;

    const previousRecord = record;
    const newRecord =
        score>previousRecord &&
        score>0;

    if(victory){
        soundRecord();

        finalTitle.textContent =
            "👑 ¡VICTORIA ABSOLUTA! 👑";

        finalTitle.style.color =
            "#ffd84d";

        finalText.innerHTML =
            `<b>${escapeHtml(player)}</b><br>`+
            `Llenaste todo el tablero.<br><br>`+
            `Puntuación: <b>${score}</b>`;

        burst(W/2,H/2,240,true);

    }else if(newRecord){
        soundRecord();

        finalTitle.textContent =
            "🏆 ¡NUEVO RÉCORD! 🏆";

        finalTitle.style.color =
            "#00f7ff";

        finalText.innerHTML =
            `<b>${escapeHtml(player)}</b><br>`+
            `Puntuación: <b>${score}</b><br><br>`+
            `🔥 Superaste el récord anterior de ${previousRecord} 🔥`;

        burst(W/2,H/2,170,true);

    }else{
        finalTitle.textContent =
            "💥 GAME OVER 💥";

        finalTitle.style.color =
            "#ffffff";

        finalText.innerHTML =
            `<b>${escapeHtml(player)}</b><br>`+
            `Puntuación final: <b>${score}</b><br>`+
            `Récord: <b>${record}</b>`;

        burst(W/2,H/2,45,true);
    }

    endOverlay.classList.remove("hidden");

    await saveScore();
}


function togglePause(){
    if(!playing){
        return;
    }

    paused = !paused;

    pauseOverlay.classList.toggle(
        "hidden",
        !paused
    );

    soundPause();

    if(paused){
        if(timer){
            clearTimeout(timer);
        }

        toast("Juego pausado");

    }else{
        toast("Continuando...");

        if(timer){
            clearTimeout(timer);
        }

        loop();
    }
}


async function toggleSound(){
    soundOn = !soundOn;

    if(soundOn){
        await ensureAudio();
        tone(660,.07,"sine",.03);
    }

    updateSoundUI();

    toast(
        soundOn
        ? "🔊 Sonido activado"
        : "🔇 Sonido desactivado"
    );
}


function setDirection(newDirection){
    if(!playing || paused){
        return;
    }

    const opposite = {
        RIGHT:"LEFT",
        LEFT:"RIGHT",
        UP:"DOWN",
        DOWN:"UP"
    };

    if(newDirection !== opposite[direction]){
        nextDirection = newDirection;
    }
}


// =========================================================
// DIBUJO
// =========================================================

function drawGrid(){
    ctx.strokeStyle = "#18243a";
    ctx.lineWidth = 1;

    for(let x=CELL;x<W;x+=CELL){
        ctx.beginPath();
        ctx.moveTo(x,0);
        ctx.lineTo(x,H);
        ctx.stroke();
    }

    for(let y=CELL;y<H;y+=CELL){
        ctx.beginPath();
        ctx.moveTo(0,y);
        ctx.lineTo(W,y);
        ctx.stroke();
    }
}


function drawObstacle(o){
    const gradient =
        ctx.createLinearGradient(
            o.x,o.y,
            o.x+CELL,o.y+CELL
        );

    gradient.addColorStop(0,"#a27bff");
    gradient.addColorStop(1,"#532da4");

    ctx.shadowColor = "#8d62ff";
    ctx.shadowBlur = 8;

    ctx.fillStyle = gradient;
    ctx.fillRect(
        o.x+2,
        o.y+2,
        CELL-4,
        CELL-4
    );

    ctx.shadowBlur = 0;

    ctx.strokeStyle = "#c1a8ff";
    ctx.strokeRect(
        o.x+4,
        o.y+4,
        CELL-8,
        CELL-8
    );
}


function drawFood(){
    if(!food){
        return;
    }

    const cx = food.x+CELL/2;
    const cy = food.y+CELL/2;

    if(food.type==="gold"){
        /*
         * DORADA MUY VISIBLE:
         * halo + círculo + estrella.
         */
        ctx.save();

        ctx.shadowColor = "#ffd84d";
        ctx.shadowBlur = 24;

        const glow =
            ctx.createRadialGradient(
                cx,cy,1,
                cx,cy,CELL
            );

        glow.addColorStop(0,"#ffffff");
        glow.addColorStop(.35,"#ffe66b");
        glow.addColorStop(1,"#ff9d00");

        ctx.fillStyle = glow;

        ctx.beginPath();
        ctx.arc(
            cx,
            cy,
            CELL/2-1,
            0,
            Math.PI*2
        );
        ctx.fill();

        ctx.shadowBlur = 0;

        ctx.fillStyle = "#6d3d00";
        ctx.font = "bold 13px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("★",cx,cy+1);

        ctx.restore();

    }else{
        ctx.save();

        ctx.shadowColor = "#ff416c";
        ctx.shadowBlur = 12;

        const gradient =
            ctx.createLinearGradient(
                food.x,
                food.y,
                food.x+CELL,
                food.y+CELL
            );

        gradient.addColorStop(0,"#ff416c");
        gradient.addColorStop(1,"#ff4b2b");

        ctx.fillStyle = gradient;

        ctx.beginPath();
        ctx.arc(
            cx,
            cy,
            CELL/2-2,
            0,
            Math.PI*2
        );
        ctx.fill();

        ctx.restore();
    }
}


function drawSnake(){
    snake.forEach((segment,index)=>{
        const gradient =
            ctx.createLinearGradient(
                segment.x,
                segment.y,
                segment.x+CELL,
                segment.y+CELL
            );

        if(index===0){
            gradient.addColorStop(
                0,
                "#5dff9a"
            );

            gradient.addColorStop(
                1,
                "#00f7ff"
            );

            ctx.shadowColor =
                "#00f7ff";

            ctx.shadowBlur = 10;

        }else{
            gradient.addColorStop(
                0,
                "#00b4d8"
            );

            gradient.addColorStop(
                1,
                "#0068a4"
            );

            ctx.shadowBlur = 0;
        }

        ctx.fillStyle = gradient;

        ctx.beginPath();

        ctx.roundRect(
            segment.x+1,
            segment.y+1,
            CELL-2,
            CELL-2,
            index===0 ? 6 : 4
        );

        ctx.fill();

        ctx.shadowBlur = 0;

        // Ojos de la cabeza.
        if(index===0){
            ctx.fillStyle = "#001116";

            let eyes;

            if(direction==="RIGHT"){
                eyes = [
                    [segment.x+14,segment.y+5],
                    [segment.x+14,segment.y+14]
                ];
            }else if(direction==="LEFT"){
                eyes = [
                    [segment.x+5,segment.y+5],
                    [segment.x+5,segment.y+14]
                ];
            }else if(direction==="UP"){
                eyes = [
                    [segment.x+5,segment.y+5],
                    [segment.x+14,segment.y+5]
                ];
            }else{
                eyes = [
                    [segment.x+5,segment.y+14],
                    [segment.x+14,segment.y+14]
                ];
            }

            eyes.forEach(([x,y])=>{
                ctx.beginPath();
                ctx.arc(x,y,2,0,Math.PI*2);
                ctx.fill();
            });
        }
    });
}


function draw(){
    ctx.clearRect(0,0,W,H);

    const bg =
        ctx.createLinearGradient(
            0,
            0,
            W,
            H
        );

    bg.addColorStop(
        0,
        "#101827"
    );

    bg.addColorStop(
        1,
        "#080d16"
    );

    ctx.fillStyle = bg;
    ctx.fillRect(0,0,W,H);

    drawGrid();

    obstacles.forEach(drawObstacle);

    drawFood();

    particles.forEach(p=>{
        ctx.globalAlpha =
            Math.max(
                0,
                Math.min(p.life,1)
            );

        ctx.fillStyle =
            p.color;

        ctx.beginPath();

        ctx.arc(
            p.x,
            p.y,
            p.radius,
            0,
            Math.PI*2
        );

        ctx.fill();
    });

    ctx.globalAlpha = 1;

    drawSnake();
}


// =========================================================
// LOOP
// =========================================================

function getDelay(){
    const base =
        DIFFICULTIES[difficulty] ||
        DIFFICULTIES.Normal;

    return Math.max(
        48,
        base-(level-1)*8
    );
}


function loop(){
    if(!playing || paused){
        return;
    }

    update();
    draw();

    const delay = getDelay();

    const base =
        DIFFICULTIES[difficulty] ||
        DIFFICULTIES.Normal;

    speedEl.textContent =
        `${Math.round(base/delay*100)}%`;

    timer = setTimeout(
        loop,
        delay
    );
}


// =========================================================
// TECLADO - ROBUSTO PARA WASD Y FLECHAS
// =========================================================

function handleKeyDown(event){
    /*
     * Usamos event.code porque no depende de mayúsculas,
     * distribución del teclado ni Caps Lock.
     */
    const code = event.code;

    const controlledKeys = new Set([
        "ArrowUp",
        "ArrowDown",
        "ArrowLeft",
        "ArrowRight",
        "KeyW",
        "KeyA",
        "KeyS",
        "KeyD",
        "KeyP",
        "KeyM",
        "Space",
        "Escape"
    ]);

    if(controlledKeys.has(code)){
        event.preventDefault();
    }

    if(code==="ArrowUp" || code==="KeyW"){
        setDirection("UP");

    }else if(code==="ArrowDown" || code==="KeyS"){
        setDirection("DOWN");

    }else if(code==="ArrowLeft" || code==="KeyA"){
        setDirection("LEFT");

    }else if(code==="ArrowRight" || code==="KeyD"){
        setDirection("RIGHT");

    }else if(code==="KeyP"){
        togglePause();

    }else if(code==="KeyM"){
        toggleSound();

    }else if(
        code==="Space" &&
        !playing &&
        !endOverlay.classList.contains("hidden")
    ){
        restartGame();

    }else if(code==="Escape"){
        goMenu();
    }
}


/*
 * window + capture=true hace el control más resistente a
 * elementos que intenten quedarse con el teclado.
 */
window.addEventListener(
    "keydown",
    handleKeyDown,
    true
);


/*
 * Si cambias de pestaña, pausa automáticamente para
 * que no mueras mientras el navegador pierde foco.
 */
window.addEventListener(
    "blur",
    ()=>{
        if(playing && !paused){
            togglePause();
        }
    }
);


// =========================================================
// BOTONES
// =========================================================

startBtn.addEventListener(
    "click",
    startGame
);

restartBtn.addEventListener(
    "click",
    restartGame
);

menuBtn.addEventListener(
    "click",
    goMenu
);

pauseBtn.addEventListener(
    "click",
    togglePause
);

resumeBtn.addEventListener(
    "click",
    togglePause
);

soundBtn.addEventListener(
    "click",
    toggleSound
);

playerNameInput.addEventListener(
    "keydown",
    event=>{
        if(event.code==="Enter"){
            event.preventDefault();
            startGame();
        }
    }
);

document
    .querySelectorAll(".touch button")
    .forEach(button=>{
        button.addEventListener(
            "pointerdown",
            ()=>{
                setDirection(
                    button.dataset.dir
                );
            }
        );
    });


// =========================================================
// INICIALIZACIÓN
// =========================================================

snake = [
    {x:220,y:220},
    {x:200,y:220},
    {x:180,y:220}
];

food = {
    x:300,
    y:220,
    type:"gold"
};

updateSoundUI();
draw();
loadScores();
</script>

</body>
</html>
"""


# =========================================================
# RUTAS FLASK
# =========================================================

@app.route("/")
def index():
    return render_template_string(HTML)


@app.get("/api/scores")
def get_scores():
    with conectar() as conn:

        top = conn.execute("""
            SELECT
                jugador,
                score,
                dificultad,
                fecha
            FROM puntuaciones
            ORDER BY
                score DESC,
                id ASC
            LIMIT 10
        """).fetchall()

        record = conn.execute("""
            SELECT
                COALESCE(MAX(score),0)
                AS record
            FROM puntuaciones
        """).fetchone()["record"]

    return jsonify({
        "record": record,
        "top": [dict(row) for row in top]
    })


@app.post("/api/scores")
def post_score():
    data = request.get_json(silent=True) or {}

    jugador = str(
        data.get(
            "jugador",
            "Jugador"
        )
    ).strip()[:20]

    dificultad = str(
        data.get(
            "dificultad",
            "Normal"
        )
    ).strip()

    score = data.get("score")

    if not jugador:
        jugador = "Jugador"

    if dificultad not in {
        "Facil",
        "Normal",
        "Dificil"
    }:
        return jsonify({
            "error":
            "Dificultad inválida"
        }),400

    if (
        not isinstance(score,int)
        or score<0
        or score>10_000_000
    ):
        return jsonify({
            "error":
            "Puntuación inválida"
        }),400

    fecha = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with conectar() as conn:
        conn.execute("""
            INSERT INTO puntuaciones
            (
                jugador,
                score,
                dificultad,
                fecha
            )
            VALUES (?,?,?,?)
        """,(
            jugador,
            score,
            dificultad,
            fecha
        ))

        conn.commit()

    return jsonify({
        "ok":True
    }),201


if __name__ == "__main__":
    init_db()

    print("")
    print("====================================")
    print("       NEON SNAKE ULTRA")
    print("====================================")
    print("Abre:")
    print("http://127.0.0.1:5000")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )