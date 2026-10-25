const diskCountInput = document.querySelector("#disk-count");
const speedInput = document.querySelector("#speed");

const moveDisplay = document.querySelector("#moves");
const minimumDisplay = document.querySelector("#minimum");
const message = document.querySelector("#message");

const playButton = document.querySelector("#play");
const stepButton = document.querySelector("#step");
const undoButton = document.querySelector("#undo");
const resetButton = document.querySelector("#reset");

const towers = [...document.querySelectorAll(".tower")];

const colors = [
  "#f5cd78",
  "#e8a684",
  "#a9d7bf",
  "#83c3d0",
  "#b4a6dc",
  "#d0b6d0",
  "#c0d989",
  "#86b9ac"
];

let diskCount;
let pegs;
let history;
let selectedTower;
let solution;
let timer = null;
let isPlaying = false;
let lastDestination = null;

function isSolved() {
  return pegs[2].length === diskCount;
}

function setMessage(text) {
  message.textContent = text;
}

function stopPlayback() {
  clearTimeout(timer);
  timer = null;
  isPlaying = false;
  playButton.textContent = "Play solution";
}

function resetGame() {
  stopPlayback();

  diskCount = Number(diskCountInput.value);

  pegs = [
    Array.from(
      { length: diskCount },
      (_, index) => diskCount - index
    ),
    [],
    []
  ];

  history = [];
  solution = [];
  selectedTower = null;
  lastDestination = null;

  setMessage("Select a tower, then select a destination.");
  render();
}

function render() {
  towers.forEach((tower, index) => {
    const container = tower.querySelector(".disks");
    container.replaceChildren();

    tower.classList.toggle(
      "selected",
      index === selectedTower
    );

    tower.setAttribute(
      "aria-label",
      `Tower ${"ABC"[index]}, disks: ${
        pegs[index].join(", ") || "none"
      }`
    );

    pegs[index].forEach((disk, stackIndex) => {
      const element = document.createElement("span");

      element.className = "disk";
      element.textContent = disk;
      element.style.width = `${25 + disk * 8}%`;
      element.style.backgroundColor = colors[disk - 1];

      const isTopDisk =
        stackIndex === pegs[index].length - 1;

      if (index === lastDestination && isTopDisk) {
        element.classList.add("arriving");
      }

      container.append(element);
    });
  });

  moveDisplay.textContent = history.length;
  minimumDisplay.textContent = 2 ** diskCount - 1;

  undoButton.disabled = history.length === 0 || isPlaying;
  stepButton.disabled = isPlaying || isSolved();
  playButton.disabled = isSolved();
}

function performMove(source, destination) {
  const disk = pegs[source].at(-1);
  const destinationTop = pegs[destination].at(-1);

  if (disk === undefined) {
    return false;
  }

  if (
    destinationTop !== undefined &&
    destinationTop < disk
  ) {
    return false;
  }

  pegs[source].pop();
  pegs[destination].push(disk);

  history.push({ source, destination, disk });
  lastDestination = destination;

  if (isSolved()) {
    const minimum = 2 ** diskCount - 1;

    setMessage(
      `Solved in ${history.length} moves! ` +
      (history.length === minimum
        ? "You reached the minimum."
        : `The minimum is ${minimum}.`)
    );
  } else {
    setMessage(
      `Move ${history.length}: disk ${disk}, ` +
      `${"ABC"[source]} → ${"ABC"[destination]}.`
    );
  }

  return true;
}

function selectTower(index) {
  if (isPlaying || isSolved()) {
    return;
  }

  lastDestination = null;

  if (selectedTower === null) {
    if (pegs[index].length === 0) {
      setMessage("That tower is empty. Choose another.");
      return;
    }

    selectedTower = index;

    setMessage(
      `Disk ${pegs[index].at(-1)} selected. ` +
      "Choose its destination."
    );
  } else if (selectedTower === index) {
    selectedTower = null;
    setMessage("Selection cleared.");
  } else {
    const moved = performMove(selectedTower, index);

    if (!moved) {
      setMessage(
        "Invalid move: a larger disk cannot sit on a smaller disk."
      );
      return;
    }

    selectedTower = null;

    // Manual moves change the state, so rebuild any future plan.
    solution = [];
  }

  render();
}

/*
  Build a recursive solution from the current board.

  This also works after the player has made manual moves.
  A simulated board lets us plan without changing the real game.
*/
function buildSolution() {
  const simulated = pegs.map(stack => [...stack]);
  const moves = [];

  function gather(number, destination) {
    if (number === 0) {
      return;
    }

    const source = simulated.findIndex(
      stack => stack.includes(number)
    );

    if (source === destination) {
      gather(number - 1, destination);
      return;
    }

    // Tower indices are 0, 1, and 2; their sum is 3.
    const spare = 3 - source - destination;

    gather(number - 1, spare);

    simulated[destination].push(simulated[source].pop());
    moves.push({ source, destination });

    gather(number - 1, destination);
  }

  gather(diskCount, 2);
  return moves;
}

function makeNextMove() {
  if (isSolved()) {
    return;
  }

  selectedTower = null;

  if (solution.length === 0) {
    solution = buildSolution();
  }

  const next = solution.shift();

  if (next) {
    performMove(next.source, next.destination);
  }

  render();
}

function animateSolution() {
  if (!isPlaying) {
    return;
  }

  makeNextMove();

  if (isSolved()) {
    stopPlayback();
    render();
    return;
  }

  const delay = 1500 - Number(speedInput.value) * 240;
  timer = setTimeout(animateSolution, delay);
}

playButton.addEventListener("click", () => {
  if (isPlaying) {
    stopPlayback();
    render();
    return;
  }

  isPlaying = true;
  playButton.textContent = "Pause";
  animateSolution();
});

stepButton.addEventListener("click", makeNextMove);

undoButton.addEventListener("click", () => {
  stopPlayback();

  const previous = history.pop();

  if (!previous) {
    return;
  }

  pegs[previous.source].push(
    pegs[previous.destination].pop()
  );

  selectedTower = null;
  solution = [];
  lastDestination = null;

  setMessage("Move undone.");
  render();
});

resetButton.addEventListener("click", resetGame);
diskCountInput.addEventListener("change", resetGame);

towers.forEach((tower, index) => {
  tower.addEventListener("click", () => selectTower(index));
});

resetGame();