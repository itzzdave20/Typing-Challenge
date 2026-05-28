const wordsByCategory = {
  Coding: [
    "python", "kivy", "function", "variable", "compile", "debug", "syntax", "algorithm",
    "iterate", "recursion", "dictionary", "exception", "package", "terminal", "keyboard"
  ],
  Common: [
    "speed", "typing", "game", "challenge", "accuracy", "practice", "focus", "energy",
    "future", "improve", "moment", "friend", "window", "planet", "simple"
  ],
  Nature: [
    "forest", "river", "mountain", "ocean", "valley", "meadow", "canyon", "volcano",
    "waterfall", "glacier", "sunset", "thunder", "rainbow", "bamboo"
  ],
  Food: [
    "pizza", "burger", "sushi", "pasta", "salad", "sandwich", "pancake", "waffle",
    "avocado", "broccoli", "chocolate", "vanilla", "cinnamon", "blueberry"
  ],
  Sports: [
    "basketball", "football", "soccer", "tennis", "volleyball", "baseball", "hockey",
    "swimming", "cycling", "marathon", "sprint", "stadium", "referee"
  ],
  Science: [
    "physics", "chemistry", "biology", "astronomy", "experiment", "molecule", "electron",
    "gravity", "telescope", "microscope", "hypothesis", "quantum"
  ]
};

const difficultySettings = {
  easy: { seconds: 60, lives: 5, points: 8 },
  medium: { seconds: 45, lives: 3, points: 12 },
  hard: { seconds: 30, lives: 2, points: 18 }
};

const state = {
  running: false,
  player: "Player",
  category: "Coding",
  difficulty: "medium",
  currentWord: "",
  score: 0,
  lives: 3,
  timeLeft: 45,
  typed: 0,
  correct: 0,
  streak: 0,
  timer: null
};

const $ = (id) => document.getElementById(id);

function init() {
  const category = $("category");
  Object.keys(wordsByCategory).forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    category.appendChild(option);
  });

  $("startGame").addEventListener("click", startGame);
  $("answer").addEventListener("keydown", handleAnswer);
  $("skipWord").addEventListener("click", skipWord);
  $("endGame").addEventListener("click", endGame);
  $("resetScores").addEventListener("click", resetScores);

  renderScores();
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
}

function startGame() {
  const difficulty = $("difficulty").value;
  const settings = difficultySettings[difficulty];

  state.running = true;
  state.player = $("playerName").value.trim() || "Player";
  state.category = $("category").value;
  state.difficulty = difficulty;
  state.score = 0;
  state.lives = settings.lives;
  state.timeLeft = settings.seconds;
  state.typed = 0;
  state.correct = 0;
  state.streak = 0;

  $("setup").classList.add("hidden");
  $("game").classList.remove("hidden");
  $("answer").value = "";
  $("answer").focus();
  $("message").textContent = "Type the word and press Enter.";

  nextWord();
  renderStats();
  clearInterval(state.timer);
  state.timer = setInterval(tick, 1000);
}

function tick() {
  state.timeLeft -= 1;
  if (state.timeLeft <= 0) {
    state.timeLeft = 0;
    renderStats();
    endGame();
    return;
  }
  renderStats();
}

function handleAnswer(event) {
  if (event.key !== "Enter" || !state.running) return;

  const answer = $("answer").value.trim().toLowerCase();
  state.typed += 1;

  if (answer === state.currentWord) {
    state.correct += 1;
    state.streak += 1;
    const bonus = Math.min(10, state.streak);
    state.score += difficultySettings[state.difficulty].points + bonus;
    $("message").textContent = `Correct. Streak: ${state.streak}`;
    nextWord();
  } else {
    state.streak = 0;
    state.lives -= 1;
    $("message").textContent = "Miss. Try the next one.";
    nextWord();
    if (state.lives <= 0) endGame();
  }

  $("answer").value = "";
  renderStats();
}

function skipWord() {
  if (!state.running) return;
  state.typed += 1;
  state.streak = 0;
  state.lives -= 1;
  $("message").textContent = "Skipped.";
  nextWord();
  renderStats();
  if (state.lives <= 0) endGame();
}

function nextWord() {
  const words = wordsByCategory[state.category];
  state.currentWord = words[Math.floor(Math.random() * words.length)];
  $("currentWord").textContent = state.currentWord;
}

function endGame() {
  if (!state.running) return;
  state.running = false;
  clearInterval(state.timer);

  saveScore();
  renderScores();
  $("setup").classList.remove("hidden");
  $("game").classList.add("hidden");
}

function renderStats() {
  $("timeLeft").textContent = state.timeLeft;
  $("score").textContent = state.score;
  $("lives").textContent = Math.max(0, state.lives);
  $("accuracy").textContent = state.typed ? Math.round((state.correct / state.typed) * 100) : 100;
}

function saveScore() {
  const scores = getScores();
  scores.push({
    player: state.player,
    score: state.score,
    accuracy: state.typed ? Math.round((state.correct / state.typed) * 100) : 100,
    category: state.category,
    difficulty: state.difficulty,
    date: new Date().toISOString()
  });
  scores.sort((a, b) => b.score - a.score);
  localStorage.setItem("typingChallengeScores", JSON.stringify(scores.slice(0, 8)));
}

function getScores() {
  try {
    return JSON.parse(localStorage.getItem("typingChallengeScores")) || [];
  } catch {
    return [];
  }
}

function renderScores() {
  const list = $("scores");
  const scores = getScores();
  list.innerHTML = "";

  if (!scores.length) {
    const item = document.createElement("li");
    item.textContent = "No scores yet.";
    list.appendChild(item);
    return;
  }

  scores.forEach((entry) => {
    const item = document.createElement("li");
    item.innerHTML = `<strong>${escapeHtml(entry.player)}</strong> - ${entry.score} pts<br>${entry.accuracy}% - ${entry.category} - ${entry.difficulty}`;
    list.appendChild(item);
  });
}

function resetScores() {
  localStorage.removeItem("typingChallengeScores");
  renderScores();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

init();
