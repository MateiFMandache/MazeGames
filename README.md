# MazeGames
Find your way through 2D and 3D mazes!

To play:
- Download files or clone the repository
- Use [Python](https://www.python.org/) to run the files
- for the 3D maze, the numpy and pygame modules are needed. You can install them using pip by typing "pip install numpy" and "pip install pygame" into the command line. If that doesn't work, you may need to [install pip](https://www.youtube.com/watch?v=Ko9b_vC6XY0).

# Extra info

For the 2D maze, the maze is automatically generated. Two algorithms for automatically generating the maze were implemented. Both start with a grid with all the edges present. The first is called "grow" and is based on growing the accessible region of the maze by randomly adding on one extra cell at a time. The second one, called "percolate", knocks down one randomly chosen wall panel at a time, provided the cells either side of the panel are not already connected. This is inspired by [percolation theory](https://en.wikipedia.org/wiki/Percolation_theory). On testing, the percolate method was found to produce more interesting mazes, so it is used by default.

For the 3D maze, I decided to opt for "do it yourself" 3D graphics rather than using a library. This made the project more interesting mathematically, however it is not great for performance as all the graphics calculations are handled by the CPU. You can choose to either play the hand-designed built in maze or a randomly generated maze. Mazes are generated using the percolate method described above.
