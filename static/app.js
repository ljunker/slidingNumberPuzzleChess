const pieces = {
    p: "♟", r: "♜", n: "♞", b: "♝", q: "♛", k: "♚",
    P: "♙", R: "♖", N: "♘", B: "♗", Q: "♕", K: "♔"
};

const files = "abcdefgh";
const boardSize = 8;
const blockSize = 2;
const squareSize = 70;
const arrowHitboxSize = 48;
const arrowTargetCenterGap = 16;
const adjacentMoves = [
    {direction: "down", fileOffset: 0, rankOffset: -2},
    {direction: "right", fileOffset: -2, rankOffset: 0},
    {direction: "left", fileOffset: 2, rankOffset: 0},
    {direction: "up", fileOffset: 0, rankOffset: 2},
];

function renderBoard(fen, inaccessible) {
    const board = document.getElementById("board");
    board.classList.remove("is-moving");
    board.innerHTML = "";

    const rows = fen.split("/");

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

    renderInaccessibleArrows(board, inaccessible);
}

function squareClicked(event) {
    const square = event.currentTarget;
    const squareName = square.dataset.square;

    alert("You clicked on square: " + squareName);
}

async function arrowClicked(event) {
    event.stopPropagation();

    const arrow = event.currentTarget;
    const board = document.getElementById("board");

    board.classList.add("is-moving");

    try {
        const response = await fetch("/slidingMove", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                direction: arrow.dataset.direction,
            }),
        });

        if (!response.ok) {
            throw new Error(`Sliding move failed with status ${response.status}`);
        }

        const data = await response.json();
        renderBoard(data.fen.split(" ")[0], data.inaccessible);
    } catch (error) {
        console.error("Error performing sliding move:", error);
        board.classList.remove("is-moving");
    }
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

function renderInaccessibleArrows(board, inaccessibleSquares) {
    const inaccessibleBlock = getInaccessibleBlock(inaccessibleSquares);

    if (!inaccessibleBlock) {
        return;
    }

    const targetCenter = getBlockCenter(inaccessibleBlock);
    const targetSquares = getBlockSquares(inaccessibleBlock);

    for (const move of adjacentMoves) {
        const sourceBlock = {
            file: inaccessibleBlock.file + move.fileOffset,
            rank: inaccessibleBlock.rank + move.rankOffset,
        };

        if (!isBlockOnBoard(sourceBlock)) {
            continue;
        }

        const sourceCenter = getBlockCenter(sourceBlock);
        const xDistance = targetCenter.x - sourceCenter.x;
        const yDistance = targetCenter.y - sourceCenter.y;
        const centerDistance = Math.hypot(xDistance, yDistance);
        const sourceEdgeInset = getBlockEdgeInset(xDistance, yDistance);
        const xUnit = xDistance / centerDistance;
        const yUnit = yDistance / centerDistance;
        const startPoint = {
            x: sourceCenter.x + xUnit * sourceEdgeInset,
            y: sourceCenter.y + yUnit * sourceEdgeInset,
        };
        const distance = centerDistance - sourceEdgeInset - arrowTargetCenterGap;
        const angle = Math.atan2(yDistance, xDistance);
        const arrow = document.createElement("button");

        arrow.type = "button";
        arrow.className = "move-arrow";
        arrow.style.left = `${startPoint.x}px`;
        arrow.style.top = `${startPoint.y - arrowHitboxSize / 2}px`;
        arrow.style.width = `${distance}px`;
        arrow.style.height = `${arrowHitboxSize}px`;
        arrow.style.transform = `rotate(${angle}rad)`;
        arrow.dataset.direction = move.direction;
        arrow.dataset.fromSquares = getBlockSquares(sourceBlock).join(",");
        arrow.dataset.toSquares = targetSquares.join(",");
        arrow.setAttribute(
            "aria-label",
            `Move ${arrow.dataset.fromSquares} ${move.direction} to ${arrow.dataset.toSquares}`
        );
        arrow.addEventListener("click", arrowClicked);

        board.appendChild(arrow);
    }
}

function getInaccessibleBlock(inaccessibleSquares) {
    const positions = inaccessibleSquares.map(squareToPosition);

    if (positions.length !== blockSize * blockSize) {
        return null;
    }

    const minFile = Math.min(...positions.map(position => position.file));
    const maxFile = Math.max(...positions.map(position => position.file));
    const minRank = Math.min(...positions.map(position => position.rank));
    const maxRank = Math.max(...positions.map(position => position.rank));

    if (maxFile - minFile !== blockSize - 1 || maxRank - minRank !== blockSize - 1) {
        return null;
    }

    return {
        file: minFile,
        rank: minRank,
    };
}

function squareToPosition(squareName) {
    return {
        file: files.indexOf(squareName[0]),
        rank: boardSize - Number(squareName.slice(1)),
    };
}

function isBlockOnBoard(block) {
    return (
        block.file >= 0
        && block.rank >= 0
        && block.file + blockSize <= boardSize
        && block.rank + blockSize <= boardSize
    );
}

function getBlockCenter(block) {
    return {
        x: (block.file + blockSize / 2) * squareSize,
        y: (block.rank + blockSize / 2) * squareSize,
    };
}

function getBlockEdgeInset(xDistance, yDistance) {
    const distance = Math.hypot(xDistance, yDistance);
    const halfBlockSize = blockSize * squareSize / 2;
    const xUnit = Math.abs(xDistance / distance);
    const yUnit = Math.abs(yDistance / distance);

    return halfBlockSize / Math.max(xUnit, yUnit);
}

function getBlockSquares(block) {
    const squares = [];

    for (let rankOffset = 0; rankOffset < blockSize; rankOffset++) {
        for (let fileOffset = 0; fileOffset < blockSize; fileOffset++) {
            const file = block.file + fileOffset;
            const rank = boardSize - (block.rank + rankOffset);
            squares.push(`${files[file]}${rank}`);
        }
    }

    return squares;
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
