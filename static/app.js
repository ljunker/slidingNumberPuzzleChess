const inaccessibleSquares = new Set([
    "a1",
    "b2",
    "e4",
    "h8"
]);

const pieces = {
    p: "♟", r: "♜", n: "♞", b: "♝", q: "♛", k: "♚",
    P: "♙", R: "♖", N: "♘", B: "♗", Q: "♕", K: "♔"
};

function renderBoard(fen, inaccessible) {
    const board = document.getElementById("board");
    board.innerHTML = "";
    console.log(inaccessible);

    const rows = fen.split("/");
    const files = "abcdefgh";

    for (let rank = 0; rank < 8; rank++) {
        let file = 0;

        for (const char of rows[rank]) {
            if (/\d/.test(char)) {
                const emptyCount = Number(char);

                for (let i = 0; i < emptyCount; i++) {
                    const squareName = `${files[file]}${8 - rank}`;
                    const square = createSquare(rank, file, squareName, null, inaccessible);
                    board.appendChild(square);
                    file++;
                }
            } else {
                const squareName = `${files[file]}${8 - rank}`;
                const square = createSquare(rank, file, squareName, char, inaccessible);

                const piece = document.createElement("span");
                piece.className = "piece";
                piece.textContent = pieces[char];
                square.appendChild(piece);

                board.appendChild(square);
                file++;
            }
        }
    }
}

function squareClicked(event) {
    const square = event.currentTarget;
    const squareName = square.dataset.square;

    alert("You clicked on square: " + squareName);
}

function createSquare(rank, file, squareName, piece, inaccessibleSquares) {
    const square = document.createElement("div");
    const isLight = (rank + file) % 2 === 0;
    const accessible = !inaccessibleSquares.includes(squareName);

    square.className = `square ${isLight ? "light" : "dark"}`;

    if (!accessible) {
        square.classList.add("inaccessible");
    }

    square.dataset.square = squareName;
    square.addEventListener("click", squareClicked);

    return square;
}

function initNewGame() {
    fetch("/newGame")
        .then(response => response.json())
        .then(data => {
            renderBoard(data.fen.split(" ")[0], data.inaccessible);
        })
        .catch(error => {
            console.error("Error starting new game:", error);
        });
}

initNewGame();