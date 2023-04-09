## Imports
# Built-ins
import tkinter as tk
import time

# Pypi
import numpy

# Custom
pass

# The number of pixels of each side of a box
BASE_LEN = 25
# The dimensions of the playable space in blocks
GAME_WIDTH = 16
GAME_HEIGHT = 25
# The rate at which difficulty increases
GAME_DIFFICULTY_RATE = 0.1
# The difficult the game starts at in updates / second
GAME_BASE_DIFFICULTY = 5.0
# The various shapes that the game uses along with each rotation
shapes = [
    {'name': 'I', 'colour': '#55FFAA', 'parts': (
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((1, 1), (1, 0), (1, -1), (1, -2))
    )},
    {'name': 'Z', 'colour': '#FFFF55', 'parts': (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (0, 1), (0, 2))
    )},
    {'name': 'S', 'colour': '#FF8888', 'parts': (
        ((0, 1), (1, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2))
    )},
    {'name': 'T', 'colour': '#FF88FF', 'parts': (
        ((0, 0), (1, 0), (2, 0), (1, 1)),
        ((2, 0), (2, 1), (2, 2), (1, 1)),
        ((0, 1), (1, 1), (2, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1))
    )},
    {'name': 'L', 'colour': '#888888', 'parts': (
        ((0, 0), (0, 1), (0, 2), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0))
    )},
    {'name': 'J', 'colour': '#FFDDCC', 'parts': (
        ((1, 0), (1, 1), (1, 2), (0, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1))
    )},
    {'name': 'O', 'colour': '#88FF55', 'parts': (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    )}
]
# A convenience function to make it shorter to make and grid widgets
def widgetgrid(widget, widget_options, grid_options):
    # Create the widget
    outval = widget(**widget_options)
    # Grid the widget
    outval.grid(**grid_options)
    # Return the widget handle
    return outval
# A standardized timing function
def gt(start=0.0):
    return time.perf_counter() - start
# The main class which contains all the game logic
class TetrisMainWindow():
    '''
    Typical use case:
        import tkinter as tk
        root = tk.Tk()
        mw = TetrisMainWindow(root)
        root.mainloop()
    '''
    def __init__(self, root):
        self.master = root
        self.master.title('Tetris-Like')
        # Store the run_id so that previous runs' processes can be ended
        self.run_id = 0
        # keys stores the user inputs
        self.keys = []
        # The game variables
        # How many game updates / second to perform
        self.update_rate = None
        # How many stones have been played
        self.stone_count = None
        # How many rows have been cleared
        self.cleared_count = None
        # The last update time (to determine when to perform the next update)
        self.last_update = None
        # The current position of the active stone
        self.current_pos = None
        # The active stone (stored as a refernce to s shapes object)
        self.current_piece = None
        # The various tkinter.Grid handles for the blocks in the stone
        self.current_piece_handles = None
        # The current rotation (stored as a int index to the shapes.pieces)
        self.current_piece_rot = None
        # The next piece to be played
        self.preview_piece = None
        # The timestamp of the first update
        self.first_update = None
        # A list of all blocks references to facilitate updating
        self.all_blocks = []
        # A random number generator to generate next block types
        self.rng = numpy.random.default_rng()
        # The mainframe contains all of the stuff in the game window
        self.mainframe = widgetgrid(tk.Frame, {'master': self.master},
            {'row': 0, 'column': 0})
        # A title for the game (not the window)
        self.titlelabel = widgetgrid(tk.Label,
            {'master': self.mainframe, 'text':'Tetris-Like'},
            {'row': 0, 'column': 0, 'columnspan': 99})
        # This frame and canvas draw the preview piece
        self.previewframe = widgetgrid(tk.Frame, {'master':self.mainframe},
            {'row': 1, 'column': 0, 'rowspan': 19})
        self.previewcanvas = widgetgrid(tk.Canvas,
            {'master': self.previewframe, 'width': 6 * BASE_LEN,
                'height': 4 * BASE_LEN, 'bg': '#222222'},
            {'row': 0, 'column': 0})
        # This frame and canvas draws the playable space
        self.gameframe = widgetgrid(tk.Frame, {'master': self.mainframe},
            {'row': 20, 'column': 0, 'columnspan': 99})
        self.gamecanvas = widgetgrid(tk.Canvas,
            {'master': self.gameframe, 'width': GAME_WIDTH * BASE_LEN,
                'height': GAME_HEIGHT * BASE_LEN, 'bg': '#222222'},
            {'row': 0, 'column': 0})
        
        # This label helps the user determine difficulty level by 
        #   showing updates/second
        self.speedlabel = widgetgrid(tk.Label,
            {'master': self.mainframe, 'text': ''}, {'row': 1, 'column': 1})
        # This label indicates if the game is running or player has died
        self.statuslabel = widgetgrid(tk.Label,
            {'master': self.mainframe, 'text': ''}, {'row': 2, 'column': 1})
        # This label shows the number of stones played
        self.countlabel = widgetgrid(tk.Label,
            {'master': self.mainframe, 'text': ''}, {'row': 3, 'column': 1})
        # This label shows the number of cleared lines
        self.clearedlabel = widgetgrid(tk.Label,
            {'master': self.mainframe, 'text': ''}, {'row': 4, 'column': 1})
        # This button allows the user to start a fresh game
        self.resetbutton = widgetgrid(tk.Button,
            {'master': self.mainframe, 'text': 'Restart',
                'command': self._setup},
            {'row': 10, 'column': 1})
        
        # This calls our _keydown function for key presses anywhere on 
        #   our window so that we can process the use input
        self.master.bind('<KeyPress>', self._keydown)
        # Run the setup and start running
        #   This can be removed to have the user click "Reset" to start
        self._setup()
        
    def _setup(self):
        # Clear out the playable space and reset all the variables
        self.gamecanvas.delete('all')
        self.stone_count = 0
        self.cleared_count = 0
        self.last_update = gt()
        # Spawn a new piece at the middle top
        self.current_pos = [GAME_WIDTH // 2, 0]
        self.current_piece = shapes[0]
        self.current_piece_handles = self._draw_shape(self.current_piece,
            self.gamecanvas, self.current_pos)
        self.current_piece_rot = 0
        # Load the next piece into the preview window
        self.preview_piece = shapes[self.rng.integers(len(shapes))]
        # Record the first update time to calculate difficulty level later
        self.first_update = gt()
        # Reset the tracker for all the "locked" blocks on the screen
        self.all_blocks = []
        # Reset the difficulty
        self.update_rate = GAME_BASE_DIFFICULTY
        # Set the text to running
        self.statuslabel.config(text='Running . . .')
        # Record the run_id and start the game
        self.run_id += 1
        self.master.after(1, self._update, self.run_id)
    
    def _check_collisions(self, shape=None, pos=None, rot=None):
        # Check to see if a shape collides with any of the "locked" blocks
        #   True indicates a collision
        # Default to the current_piece for convenience
        shape = shape or self.current_piece 
        pos = pos or self.current_pos
        rot = rot or self.current_piece_rot
        # Load the pertinent "locked" blocks
        #   preprocessed to make the loop simpler
        all_blocks = [[block[0], block[1]] for block in self.all_blocks]
        # Check each block in the provided or current piece to see if it
        #   conflicts with any others
        for part in shape['parts'][rot % len(shape['parts'])]:
            # Calculate the block position
            #   (position + partoffset + movementdown)
            next_position = [pos[0] + part[0], pos[1] + part[1] + 1]
            # Verify the block does not overlap another
            if next_position in all_blocks or next_position[1] >= GAME_HEIGHT:
                return True
            # Verify the block is not too wide
            if next_position[0] < 0 or next_position[0] >= GAME_WIDTH:
                return True
            # Verify that the block is not too low
            if next_position[1] > GAME_HEIGHT:
                return True
        # If it didn't leave the bounds or overlap another block, return False
        return False
    def _redraw(self):
        # Draw the current_piece to the screen
        # Remove the old blocks
        for handle in self.current_piece_handles:
            self.gamecanvas.delete(handle['handle'])
        # Draw the new blocks and store the handles for the next call to
        #   this function or to "lock" them
        self.current_piece_handles = self._draw_shape(self.current_piece,
            self.gamecanvas, self.current_pos, self.current_piece_rot)
    def _update(self, run_id):
        # Update the game window
        # If this function call is old (from a previous run), stop
        if not run_id == self.run_id:
            return
        check_collision = False
        # Process user input
        if len(self.keys):
            # This stores the lateral translation input
            translateval = 0
            # This stores the rotation input
            rotval = 0
            if 'Up' in self.keys:
                rotval = 1
            if 'Left' in self.keys:
                translateval += -1
            if 'Right' in self.keys:
                translateval += 1
            # If no collisions resulted from the user input, perform it
            #   and redraw
            pos=[self.current_pos[0] + translateval, self.current_pos[1]]
            rot=self.current_piece_rot + rotval
            if not self._check_collisions(pos=pos, rot=rot):
                self.current_pos[0] += translateval
                self.current_piece_rot += rotval
                self._redraw()
            # Reset the user inputs
            self.keys = []
        # Move piece
        if gt(self.last_update) > 1 / self.update_rate:
            # We moved the piece we need to check for collisions
            check_collision = True
            # Move the piece down one position
            self.current_pos[1] += 1
            # Redraw it
            self._redraw()
            # Update the last_update and update_rate
            self.update_rate = GAME_BASE_DIFFICULTY \
                + gt(self.first_update) * GAME_DIFFICULTY_RATE
            self.last_update = gt()
        # If the piece reached something, lock piece and spawn another and 
        #   kill player if necessary
        if check_collision:
            # Check for a collision
            collision_detected = self._check_collisions()
            # If there was no collision, nothing needs to be done, otherwise:
            if collision_detected:
                # Lock the piece and add its blocks to the locked blocks
                parts = self.current_piece['parts'][self.current_piece_rot \
                    % len(self.current_piece['parts'])]
                for part, parth in zip(parts, self.current_piece_handles):
                    self.all_blocks.append(
                        [self.current_pos[0] + part[0],
                            self.current_pos[1] + part[1],
                            parth['handle'],
                            self.current_piece['colour']
                        ]
                    )
                # Check for and perform row clearance
                self._process_row_clearance()
                # Reset the current piece data
                self.current_piece_handles = []
                self.current_piece_rot = 0
                self.current_piece = self.preview_piece
                self.current_pos = [GAME_WIDTH // 2, 0]
                # Generate a new preview piece
                self.preview_piece = shapes[self.rng.integers(len(shapes))]
                # Reset the preview canvas and draw the next preview to it
                self.previewcanvas.delete('all')
                self._draw_shape(self.preview_piece, self.previewcanvas, 
                    (1, 1), self.current_piece_rot)
                # Increment the stone count
                self.stone_count += 1
                self.countlabel.config(
                    text='Stone count : {0}'.format(self.stone_count))
                # If the new piece has collisions, kill the player 
                #   (i.e., no space to spawn a new piece)
                kill_player = self._check_collisions()
                # Set update_rate to 0 and change text to dead, #
                #   and do not recall this function
                if kill_player:
                    self.update_rate = 0
                    self.statuslabel.config(text='Dead :(')
                    return
        
        # Reset labels and _update function
        self.speedlabel.config(
            text='Game speed: {0:.1f}'.format(self.update_rate))
        self.clearedlabel.config(
            text='Rows cleared: {0}'.format(self.cleared_count))
        self.master.after(1, self._update, run_id)
    def _process_row_clearance(self):
        # Check for row removals
        # Hold a flag to indicate if a redraw is necessary
        redraw = False
        # Check each row for fullness
        for row_num in range(GAME_HEIGHT):
            # Count how many blocks are in this row
            row_count = sum([block[1] == row_num for block in self.all_blocks])
            # If the row is full
            if row_count == GAME_WIDTH:
                redraw = True
                self.cleared_count += 1
                # Remove the blocks in that row
                for block in self.all_blocks[::-1]:
                    if block[1] == row_num:
                        self.gamecanvas.delete(block[2])
                        self.all_blocks.remove(block)
                    elif block[1] < row_num:
                        # If this bock was above the removed block,
                        #   move it down one
                        block[1] += 1
        # Redraw all the blocks to the screen
        if redraw:
            for block in self.all_blocks:
                # Delete the old block and draw the new one,
                #   then store the handles for the future
                self.gamecanvas.delete(block[2])
                new_handle = self._draw_shape(
                    {'parts':[[(0,0)]], 'colour': block[3]},
                    self.gamecanvas, block)
                block[2] = new_handle
    def _keydown(self, e):
        # When a user presses a key, record that
        #   This can be updated to operate continuously
        self.keys.append(e.keysym)
    def _draw_shape(self, shape, canvas, location=None, rot=None):
        # Draw a shape to the canvas provided
        #   Default location and rotation for convenience
        location = location or (0, 0)
        rot = rot or 0
        handles = []
        # Draw each block of the shape and record the handles
        #   returned by canvas
        for part in shape['parts'][rot % len(shape['parts'])]:
            x = location[0] + part[0]
            y = location[1] + part[1]
            handlex = canvas.create_rectangle(
                x * BASE_LEN, y * BASE_LEN, 
                (x + 1) * BASE_LEN, (y + 1) * BASE_LEN,
                fill=shape['colour'])
            handles.append({'x': x, 'y': y, 'handle': handlex})
        # Return the handles to the calling function
        return handles

def _main():
    root = tk.Tk()
    mw = TetrisMainWindow(root)
    root.mainloop()

if __name__ == '__main__':
    _main()