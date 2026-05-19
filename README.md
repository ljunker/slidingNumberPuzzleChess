# Sliding Number Puzzle Chess

Eine kleine Flask-Webapp für eine Schachvariante mit einem verschiebbaren 2x2-Loch im Brett. Inspiriert von xkcd
3139, ["Chess Variant"](https://xkcd.com/3139/).

## Start

```sh
uv run flask --app app run --port 8765
```

Dann im Browser öffnen:

```text
http://127.0.0.1:8765
```

## Spielidee

- Weiß wird vom Spieler gesteuert.
- Schwarz wird von einer einfachen KI gespielt.
- Das Brett enthält ein inaccessible 2x2-Feld, intern mit `x` markiert.
- Figuren können normal ziehen, soweit der Zug legal ist und den eigenen König nicht im Schach lässt.
- Das inaccessible 2x2-Feld kann per Pfeil verschoben werden. Ein Sliding-Move zählt als vollwertiger Zug.
- Schach, Schachmatt und Patt werden berücksichtigt.

## KI

Die KI-Suchtiefe kann im Browser von `2` bis `10` eingestellt werden. Die KI bewertet Material, Mobilität, einfache
Positionswerte und berücksichtigt sowohl Figurenzüge als auch Sliding-Moves.

## Notation

Die Partie wird rechts neben dem Brett mitgeschrieben.

- Normale Züge: `e2-e4`, `Sg1-f3`, `Ta1-e1+`
- Schlagzüge: `d5xc4`
- Schach: `+`
- Schachmatt: `#`
- Sliding-Züge: `SL↑ c2-d1→c4-d3`

Bei Sliding-Zügen beschreibt der erste Block den verschobenen 2x2-Bereich und der zweite Block das Ziel, also das vorher
inaccessible 2x2-Feld.
