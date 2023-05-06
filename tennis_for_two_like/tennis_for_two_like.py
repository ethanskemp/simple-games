## Imports
# Built-ins
import tkinter as tk
import time

# Pypi
import numpy as np

# Custom
pass

# The size of the court area
COURT_WIDTH = 800
COURT_HEIGHT = 400
# The buffer around the edge
COURT_LINE_FRAC = 0.1
# The thickness of the court and net
COURT_LINE_THICK = 5
# The edges of the court box on the bottom
COURT_BOUNDS = [
    COURT_LINE_FRAC * COURT_WIDTH,
    (1 - COURT_LINE_FRAC) * COURT_HEIGHT - COURT_LINE_THICK,
    (1 - COURT_LINE_FRAC) * COURT_WIDTH,
    (1 - COURT_LINE_FRAC) * COURT_HEIGHT
]
# The edges of the net barrier in the middle
NET_BOUNDS = [
    COURT_WIDTH // 2 - COURT_LINE_THICK // 2, 
    COURT_HEIGHT * (1 - 2 * COURT_LINE_FRAC) - 2 *  COURT_LINE_THICK,
    COURT_WIDTH // 2 + COURT_LINE_THICK // 2, 
    COURT_HEIGHT * (1 - COURT_LINE_FRAC) - 2 * COURT_LINE_THICK
]
# The radius of ball
BALL_RADIUS = 5
# The speed the ball comes off the paddle at
BALL_VELOCITY = 0.6 * COURT_WIDTH   # pixels / second
# The local acceleration due to gravity
GRAVITY = 0.3 * COURT_WIDTH         # pixels / second ^ 2
# How much the ball slows down while traveling through air
AIR_RESISTANCE = 0.4                # 1 / seconds
# The background colour around the court
FIELD_COLOUR = '#444444'
# The default colour for most things drawn in the game
COURT_COLOUR = '#A0B0C0'
# The colour of the player input box area
INPUT_BOX_COLOUR = '#222222'
# The width of the player input boxes on the sides
INPUT_BOX_WIDTH = COURT_WIDTH / 4
# How wide to draw the player input arc
INPUT_ARC_WIDTH = 10 # degrees
# The min/max angles the ball can be struck at
INPUT_MIN = -15.0 # degrees
INPUT_MAX = 55.0  # degrees
# How fast to steer the paddles while holding down the key
INPUT_RATE = 150.0 # degrees / second

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

class TennisForTwoMainWindow():
    '''
    Typical use case:
        import tkinter as tk
        root = tk.Tk()
        mw = TennisForTwoMainWindow(root)
        root.mainloop()
    '''
    def __init__(self, root):
        self.master = root
        self.master.title('Tennis For Two Like')
        # The mainframe contains all of the game content
        self.mainframe = widgetgrid(
            tk.Frame, {'master': self.master},
            {'row': 0, 'column': 0})
        # The main game screen where the ball and court are
        self.mainview = widgetgrid(
            tk.Canvas,
            {'master': self.mainframe, 'width': COURT_WIDTH,
                'height': COURT_HEIGHT, 'bg': FIELD_COLOUR},
            {'row': 2, 'column': 1}
        )
        # The player input areas, added since there is no dial to feel
        self.player_canvas_left = widgetgrid(
            tk.Canvas,
            {'master': self.mainframe, 'width': INPUT_BOX_WIDTH,
                'height': COURT_HEIGHT, 'bg': INPUT_BOX_COLOUR},
            {'row': 2, 'column': 0}
        )
        self.player_canvas_right = widgetgrid(
            tk.Canvas,
            {'master': self.mainframe, 'width': INPUT_BOX_WIDTH,
                'height': COURT_HEIGHT, 'bg': INPUT_BOX_COLOUR},
            {'row': 2, 'column': 2}
        )
        # Some text above each player input to guide usage
        self.player_instructions_left = widgetgrid(
            tk.Label,
            {'master': self.mainframe, 'text': 'W/S to move\nD to strike'},
            {'row': 1, 'column': 0}
        )
        self.player_instructions_right = widgetgrid(
            tk.Label,
            {'master': self.mainframe, 
                'text': 'Up/Down to move\nLeft to strike'},
            {'row': 1, 'column': 2}
        )
        # A label to display the score each player has acrued
        self.player_score_left_label = widgetgrid(
            tk.Label,
            {'master': self.mainframe, 'text': 'Score: 0'},
            {'row': 0, 'column': 0}
        )
        self.player_score_right_label = widgetgrid(
            tk.Label,
            {'master': self.mainframe, 'text': 'Score: 0'},
            {'row': 0, 'column': 2}
        )
        # Capture the key presses so that players can aim and strike
        self.master.bind('<KeyPress>', self._keydown)
        self.master.bind('<KeyRelease>', self._keyup)
        # The player scores
        self.player_score_left = 0
        self.player_score_right = 0
        # A handle for the ball on the mainview canvas
        self.ball = None
        # The angle each player has steered to that the ball will leave at
        self.player_input_left = 0.0
        self.player_input_right = 180.0
        # The handles for the arc drawn on the input window
        self.player_input_handle_left = None
        self.player_input_handle_right = None
        # What keys are being held down
        self.inputs = set()
        # Record each input time so that we can calc total angle change
        self.last_input_time = None # 0.0
        # The velocity of the ball
        self.ball_velocity = None # [0.0, 0.0]
        # The player that struck the ball last
        self.last_strike = None # 'left' or 'right'
        # How many times the ball has bounced
        self.bounces = None
        # Whether or not the game is still running
        self.running = False
        
        # Draw the field components (net, court)
        self._draw_field()
        # Draw the player input arcs
        self._draw_player_inputs()
        # Setup the game and get ready to start
        self._setup()
    
    def _keydown(self, event):
        # Capture all the keys that are pressed down
        #   Keys remain in this set until released
        self.inputs.add(event.keysym)
    
    def _keyup(self, event):
        # Remove keys from the set when they are released
        if event.keysym in self.inputs:
            self.inputs.remove(event.keysym)
        else:
            pass # Orphan key?
    
    def _draw_field(self):
        # A short function to draw the field and net on the screen
        self.court = self.mainview.create_rectangle(
            *COURT_BOUNDS,
            fill=COURT_COLOUR,
            outline=COURT_COLOUR
        )
        self.net = self.mainview.create_rectangle(
            *NET_BOUNDS,
            fill=COURT_COLOUR,
            outline=COURT_COLOUR
        )
    def _setup(self):
        # If a ball is already on the screen, get rid of it
        if not self.ball is None:
            self.mainview.delete(self.ball)
        # Draw a new ball on the screen
        self.ball = self.mainview.create_oval(
            COURT_LINE_FRAC * COURT_WIDTH - BALL_RADIUS,
            (1 - COURT_LINE_FRAC) * COURT_HEIGHT \
                - 3 * COURT_LINE_THICK - BALL_RADIUS,
            COURT_LINE_FRAC * COURT_WIDTH + BALL_RADIUS,
            (1 - COURT_LINE_FRAC) * COURT_HEIGHT \
                - 3 * COURT_LINE_THICK + BALL_RADIUS,
            fill=COURT_COLOUR,
            outline=COURT_COLOUR
        )
        # Pre-initialize session variables to standard values
        self.player_input_left = 0.0
        self.player_input_right = 180.0
        self.inputs.clear()
        self.last_input_time = None
        self.last_update_time = gt()
        self.ball_velocity = [0.0, 0.0]
        self.last_strike = None
        self.bounces = 0
        # Start the game (ball moves only after a player hits strike)
        self.running = True
        self.master.after(1, self._update)
        
    def _update(self):
        if not self.running:
            return
        
        dt = gt(self.last_update_time)
        self.last_update_time = gt()
        
        left_strike, right_strike = self._process_player_inputs()
        self._draw_player_inputs()
        
        player_scored_left = False
        player_scored_right = False
        
        ball_pos = self.mainview.coords(self.ball)
        ball_pos = [
            (ball_pos[0] + ball_pos[2]) / 2,
            (ball_pos[1] + ball_pos[3]) / 2
        ]
        # Process user inputs and gravity
        if left_strike \
                and ball_pos[0] < COURT_WIDTH // 2 \
                and self.ball_velocity[0] <= 0.0:
            # If the ball is moving left, on the left side and left player
            #   hits strike, then process the strike
            self.ball_velocity = [
                BALL_VELOCITY * np.cos(np.radians(self.player_input_left)),
                -BALL_VELOCITY * np.sin(np.radians(self.player_input_left))
            ]
            self.last_strike = 'left'
            self.bounces = 0
            
        elif right_strike \
                and ball_pos[0] > COURT_WIDTH // 2 \
                and self.ball_velocity[0] >= 0.0:
            # If the ball is moving right, on the right side and right player
            #   hits strike, then process the strike
            self.ball_velocity = [
                BALL_VELOCITY * np.cos(np.radians(self.player_input_right)),
                -BALL_VELOCITY * np.sin(np.radians(self.player_input_right))
            ]
            self.last_strike = 'right'
            self.bounces = 0
            
        elif np.linalg.norm(self.ball_velocity):
            # If no strikes, then process gravity
            self.ball_velocity = [
                self.ball_velocity[0],
                self.ball_velocity[1] + GRAVITY * dt
            ]
        # Handle the ball hitting the court
        if self.ball in self.mainview.find_overlapping(*COURT_BOUNDS):
            # Ball hit the court and should bounce
            self.ball_velocity = [
                self.ball_velocity[0],
                -self.ball_velocity[1]
            ]
            if ball_pos[0] < COURT_WIDTH // 2:
                if self.last_strike == 'left':
                    # Left player failed to get the ball back over the net
                    player_scored_right = True
                else:
                    self.bounces += 1
                    if self.bounces >= 2:
                        # Left player faield to hit it before it bounced
                        player_scored_right = True
            if ball_pos[0] > COURT_WIDTH // 2:
                if self.last_strike == 'right':
                    # Right player failed to get the ball back over the net
                    player_scored_left = True
                else:
                    self.bounces += 1
                    if self.bounces >= 2:
                        # Right player failed to hit it before it bounced
                        player_scored_left = True
        # Handle the ball hitting the net
        if not (player_scored_left or player_scored_left) and \
                self.ball in self.mainview.find_overlapping(*NET_BOUNDS):
            # If one of the players hits the net, the other scores
            if self.last_strike == 'left':
                player_scored_right = True
            if self.last_strike == 'right':
                player_scored_left = True
        # Handle the ball leaving the field
        if not (player_scored_left or player_scored_right):
            if ball_pos[0] < COURT_BOUNDS[0]:
                if self.last_strike == 'right':
                    if self.bounces:
                        # Right hit it, it hit the court, then exited
                        player_scored_right = True
                    else:
                        # Right hit it, it missed the court
                        player_scored_left = True
            elif ball_pos[0] > COURT_BOUNDS[2]:
                if self.last_strike == 'left':
                    if self.bounces:
                        # Left hit it, it hit the court, then exited
                        player_scored_left = True
                    else:
                        # Left hit it, it missed the court
                        player_scored_right = True
            elif ball_pos[1] < 0:
                if self.last_strike == 'left':
                    # Left hit it, it missed the court
                    player_scored_right = True
                else:
                    # Right hit it, it missed the court
                    player_scored_left = True
        # Check if a player scored
        if player_scored_left:
            # Increment the score counter
            self.player_score_left += 1
            # Update the display to show their score
            self.player_score_left_label.config(
                text='Score: {0}'.format(self.player_score_left)
            )
            # Show a temporary celebratory message on the screen
            texth = self.player_canvas_left.create_text(
                (INPUT_BOX_WIDTH / 2, 10),
                text='SCORE!', fill=COURT_COLOUR)
            # Schedule the celebratory text for deletion
            self.master.after(1000, self._del_object, 
                self.player_canvas_left, texth)
        if player_scored_right:
            # Increment the score counter
            self.player_score_right += 1
            # Update the display to show their score
            self.player_score_right_label.config(
                text='Score: {0}'.format(self.player_score_right)
            )
            # Show a temporary celebratory message on the screen
            texth = self.player_canvas_right.create_text(
                (INPUT_BOX_WIDTH / 2, 10),
                text='SCORE!', fill=COURT_COLOUR)
            # Schedule the celebratory text for deletion
            self.master.after(1000, self._del_object, 
                self.player_canvas_right, texth)
        # If one of the players scored, re-run the setup to start again
        if player_scored_left or player_scored_right:
            self._setup()
            # Do no restart this loop, setup will handle future calls
            return
        # Handle air drag
        self.ball_velocity = [
            self.ball_velocity[0] * (1 - AIR_RESISTANCE * dt),
            self.ball_velocity[1] * (1 - AIR_RESISTANCE * dt)
        ]
        # Update the ball position
        self.mainview.move(self.ball,
            self.ball_velocity[0] * dt,
            self.ball_velocity[1] * dt
        )
        # Re-call this function for the next update
        self.master.after(10, self._update)
    def _del_object(self, canvas, handle):
        # Remove an object from the canvas (called with a delay from mainloop)
        canvas.delete(handle)
    def _process_player_inputs(self):
        # Calculate time since last input update so that input rate does 
        #   not depend on update rate
        dt = gt(self.last_input_time or 0.0)
        self.last_input_time = gt()
        update_scalar = dt * INPUT_RATE
        # Check each players various inputs and update their input position
        if 'w' in self.inputs:
            self.player_input_left += update_scalar
        if 's' in self.inputs:
            self.player_input_left -= update_scalar
        if 'd' in self.inputs:
            left_strike = True
        else:
            left_strike = False
        
        if 'Up' in self.inputs:
            self.player_input_right -= update_scalar
        if 'Down' in self.inputs:
            self.player_input_right += update_scalar
        if 'Left' in self.inputs:
            right_strike = True
        else:
            right_strike = False
        # Update the player inputs and constrain it to the max range allowed
        self.player_input_left = max(INPUT_MIN,
            min(INPUT_MAX, self.player_input_left))
        self.player_input_right = min(180.0 - INPUT_MIN,
            max(180.0 - INPUT_MAX, self.player_input_right))
        # Let the calling function know that the player attempted a strike
        return left_strike, right_strike
    
    def _draw_player_inputs(self):
        # Draw the player inputs as narrow arcs on the sides of the map
        # Delete the one already present
        self.player_canvas_left.delete(self.player_input_handle_left)
        # Draw the updated one
        self.player_input_handle_left = self.player_canvas_left.create_arc(
            -INPUT_BOX_WIDTH * 0.9,
            COURT_HEIGHT // 2 - INPUT_BOX_WIDTH,
            INPUT_BOX_WIDTH * 0.9,
            COURT_HEIGHT // 2 + INPUT_BOX_WIDTH,
            start=self.player_input_left - INPUT_ARC_WIDTH // 2,
            extent=INPUT_ARC_WIDTH,
            fill=COURT_COLOUR,
            outline=COURT_COLOUR
        )
        self.player_canvas_right.delete(self.player_input_handle_right)
        self.player_input_handle_right = self.player_canvas_right.create_arc(
            INPUT_BOX_WIDTH * 0.1,
            COURT_HEIGHT // 2 - INPUT_BOX_WIDTH,
            INPUT_BOX_WIDTH * 1.9,
            COURT_HEIGHT // 2 + INPUT_BOX_WIDTH,
            start=self.player_input_right - INPUT_ARC_WIDTH // 2,
            extent=INPUT_ARC_WIDTH,
            fill=COURT_COLOUR,
            outline=COURT_COLOUR
        )

def _main():
    root = tk.Tk()
    mw = TennisForTwoMainWindow(root)
    root.mainloop()

if __name__ == '__main__':
    _main()