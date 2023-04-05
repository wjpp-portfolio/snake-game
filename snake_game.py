import pygame, random, time
from typing import Optional

CELL_SIZE_PX = 15 #the size of each logical 'square' in the game (snake, food etc) in pixels
GRID_WIDTH = 25# total number of cells wide game is
GRID_HEIGHT = 25 # total number of cells tall game is
GRID_SIZE = (GRID_HEIGHT * CELL_SIZE_PX, GRID_WIDTH * CELL_SIZE_PX) #creates tuple for easier reference of game size

MENU_HEIGHT = GRID_SIZE[0] / 2 #the coloured score area for each player.  Height is for half the board height (which needs to be an even number)
MENU_WIDTH = GRID_SIZE[1] #same for both players

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PINK = (255, 0, 255)
BLUE = (100, 175, 255)
RED = (255,55,60)
LIGHT_BLUE = (0, 255, 255)
YELLOW = (255, 255, 0)
FPS = 60

class Coordinate:
    """data class for easier access for y x values"""
    def __init__(self,tup: tuple[int,int]):
        self.y = tup[0]
        self.x = tup[1]
        self.location = tup

       
SNAKE_SPEED = 7 # max speed == FPS
NUMBER_OF_FOOD = 1 #defines how many food icons appear at any moment

UP = (-1,0)
RIGHT = (0,1)
DOWN = (1,0)
LEFT = (0,-1)

KEYS_P1 = { 
    pygame.K_w: UP,
    pygame.K_d: RIGHT,
    pygame.K_s: DOWN,
    pygame.K_a: LEFT,
}
KEYS_P2 = {
    pygame.K_UP: UP,
    pygame.K_RIGHT: RIGHT,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT
}

class Snake:
    """defines a snake object, including each segment, its speed, location, size and collision detection"""
    def __init__(self,name: str,start_yx: tuple[int,int], length: int, starting_direction: tuple[int,int], colour: tuple[int,int,int], keyset: dict): 
        self.name = name
        self.colour = colour
        self.segments = [] #holds snake segment locations as yx tuples
        self.set_speed(SNAKE_SPEED)
        self.time = 0 
        self.bound_keys = keyset
        
        for i in range(length):
            self.segments.append(Coordinate(start_yx)) #snake is bunched up on starting square
            
        self.next_intended_direction = Coordinate(starting_direction)
        self.current_direction = Coordinate(starting_direction)
    def grow(self) -> None:
        """adds extra segment to snake at same position as last segment"""
        self.segments.append(self.segments[-1])
        
    def set_speed(self,speed: int) -> None:
        """sets snake speed based on `speed` up to max of `FPS`"""
        if speed > FPS:
            raise ValueError('Snake speed greater than `FPS`') 
        if speed < 3:
            raise ValueError('Snake speed too low, inherent collision issues') 
        self.speed = 1 / speed 
    def move(self,seconds) -> None: 
        """updates the self.segments list location to move the snake.  Each segments gets the location of the segement before it except the head who gets a new location"""

        if seconds < self.time + self.speed: #defines the speed of the snake; returns if too little game time has passed
            return
                        
        if self.current_direction.y + self.next_intended_direction.y != 0 and self.current_direction.x + self.next_intended_direction.x != 0: #sets current position only if snake isn't going back on itself
            self.current_direction = self.next_intended_direction

        self.time = seconds #captures elapsed seconds for 
        
        temp_list = [] #list to hold updated location
        head_location = self.segments[0] # the current snake lead square is stored at position zero in the list
        new_head_location = Coordinate((head_location.y + self.current_direction.y,head_location.x + self.current_direction.x)) #determines next location for head based on which way the snake is facing

        temp_list.append(new_head_location)  # writes new head location of snake to temporary list

        for segment in self.segments:
            temp_list.append(segment) #appends remaining snake segments to temp list, essentially pushing them down the list by 1 position. 
        del temp_list[-1] #removes last segment location as the snake didn't get longer since this temp list is 1 item too long (due to adding new head location)

        self.segments = temp_list
        
    def collided_with_opponent(self, list_of_snakes: list) -> bool:
        """determines if snake has crashed into any other snake"""
        for snake in list_of_snakes: #list is shuffled for the sole instance where both snakes hit head-to-head.  In this case the first snake to do the check will lose but its impossible to determine who was at fault.  So randomise it and its slightly more fair
            if snake.name != self.name: #check currently iterated snake isnt self
                for other_segments in snake.segments: #iterate through segments of other snake to accses Coordinate data
                    if self.segments[0].location == other_segments.location: #check if head location is at any same locattion in other snake
                        return True
                    
    def collided_with_edge(self) -> bool:
        """returns true of snake head cell is inside the game border"""
        head = self.segments[0] #get snake head Coordinate
        if head.y < 0 or head.y >= GRID_HEIGHT or head.x < 0 or head.x >= GRID_WIDTH: #checks for border collison
            return True
        
    def collided_with_self(self) -> bool:
        """returns true if snake head segment is in same location as any of its other cells"""
        head = self.segments[0] #get snake head Coordinate
        for segs in self.segments[1:]:
            if head.location == segs.location:
                return True
class Game_Logic:
    """used to handle specific elements of gameplay such as creating food, updating snake locations, reading keys presses and validating collisions"""
    def __init__(self,players: int):
        self.food_locations = set() #contains collection of Coordinate
        self.input_read_timer = 0
        self.input_read_speed = 1 / 25
        self.snakes = []
        self.players = players
        self.snakes.append(Snake(name="Blue",start_yx=(5,3),length=5,starting_direction=RIGHT,colour=BLUE,keyset=KEYS_P2)) #init new snake
        self.the_other_player = { #easy way to identify the other snake that the one in question
                self.snakes[0].name : self.snakes[0].name  
            }
        if players == 2:
            self.snakes.append(Snake(name="Red",start_yx=(GRID_HEIGHT-5,GRID_WIDTH-5),length=5,starting_direction=LEFT,colour=RED,keyset=KEYS_P1)) #init new snake
            self.the_other_player = { #easy way to identify the other snake that the one in question
                self.snakes[0].name : self.snakes[1].name,
                self.snakes[1].name : self.snakes[0].name      
            }
     
    def create_food(self) -> None: 
        """builds list of all empty space and choses one at random for food location"""
        empty_space = [] #list to hold areas taht are not occupied by snakes
        
        for y in range(GRID_HEIGHT): #iterate through all possible locations in the game
            for x in range(GRID_WIDTH):
                tup = (y,x)
                empty_space.append(tup)

        for snake in self.snakes: #iterate each snake
            for seg in snake.segments: #iterate each list of segments
                if seg.location in empty_space: #if a snake segment appears in the available food space...      
                    empty_space.remove(seg.location) # remove that location as available         
             
        for i in range(NUMBER_OF_FOOD - len(self.food_locations)): #this loop exists to accomodate more than 1 food (if desired)
            chosen_location = random.choice(empty_space) #choose a random valid location (which doesn't ahve a snake in it)
            self.food_locations.add(Coordinate(chosen_location)) #add it to food set
            
    def move_snakes(self, delta) -> None:
        """process each snake position"""
        for snake in self.snakes:
            snake.move(delta)

    def read_key_presses(self,seconds):
        """reads user input to determine impact on each snake."""
        if seconds < self.input_read_timer + self.input_read_speed: #limits input reads to reduce excessive key presses appearing in events queue
            return

        self.input_read_timer = seconds #captures elapsed seconds for limit
 
        for event in pygame.event.get(): # returns list of events and clears queue
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN: #checks key is pressed
                for snake in self.snakes:
                    direction = snake.bound_keys.get(event.key) #check if the pressed key matches this snakes key map
                    if direction:
                        snake.next_intended_direction = Coordinate(direction)
                        continue #skip to next snake to avoid parsing a later key press

    def check_food_collision(self) -> None:
        """determines whether either snake is on the same location as a food"""
        for snake in self.snakes: #iterate snakes
            for i in self.food_locations: #iterate each Coordinate object
                if snake.segments[0].location == i.location: #check if snake contacts any food
                    self.food_locations.remove(i) #removes this food from the set
                    self.create_food()  #adds new food
                    snake.grow()
            
    def check_collisions(self) -> bool:
        """returns check snake collision with edge of map, self, and other snake.  If playing solo, the return object is the length of the snake.  For 2 players it reports the player who didn't crash"""
        for snake in sorted(self.snakes,key=lambda _: random.random()):
            #print(f'{snake.name} length: {len(snake.segments)}')
            if snake.collided_with_opponent(self.snakes) or snake.collided_with_edge() or snake.collided_with_self():
                if self.players == 1:
                    return len(snake.segments)
                else:
                    return snake.name

class Player_stats_display:
    pass
  
class Game_display:
    """draws all visible assets, including snakes, food and buttons"""
    def __init__(self):
        self.display = pygame.display.set_mode(GRID_SIZE) #set display size
        self.font = pygame.font.Font(pygame.font.get_default_font(), 25) #set fonts use for score message
        
    def show(self,game: Game_Logic) -> None:
        """draws all items to screen"""
        self.display.fill(WHITE)
        self.draw_food(game)
        self.draw_snake(game.snakes)
        pygame.display.update()
    
    def draw_game_board(self):
        pass
    
    def draw_food(self,game: Game_Logic) -> None: 
        """draws a pink square for each tuple in passed game logic set """
        for i in game.food_locations: 
            self.draw_square(i.y * CELL_SIZE_PX-1, i.x * CELL_SIZE_PX-1, CELL_SIZE_PX-1, CELL_SIZE_PX-1, PINK)

    def draw_snake(self,snakes) -> None: 
        """draws blue square for each snake segment from passed snake object"""
        for snake in snakes:
            for i in snake.segments:
                self.draw_square(i.y * CELL_SIZE_PX-1, i.x * CELL_SIZE_PX-1, CELL_SIZE_PX-1, CELL_SIZE_PX-1, snake.colour)
                
    def draw_square(self,y,x,yy,xx,colour):
        """draws squares to represent menu buttons"""
        pygame.draw.rect(
            self.display, colour,
            pygame.Rect(x,y,xx,yy,))

class Button:
    """defines a menu button object used for menu navigation."""
    def __init__(self,location: Coordinate,colour: tuple[int,int,int],text: str):
        self.background_colour = colour
        self.highlight_colour = YELLOW
        self.location = location
        
        self.button_size_modifier_px = 10 #enlarges the border around the text to make the button bigger
        self.highlight_thickness_px = 10
        self.font = pygame.font.Font(pygame.font.get_default_font(), 15) #set fonts use for score message
        self.button_text = self.font.render(text, True, BLACK)
        
        self.highlighted = False
        
        self.text_rect = self.button_text.get_rect(center=(self.location.x,self.location.y)) #creates a rectange around the text and centered on it
        #self.text_rect.left -= self.text_rect.width / 2 #shifts the buttom left by half its width to be center aligned so that buttom init coordinates are the center of the buttom, not the top left
        self.button_rect = pygame.Rect(
            self.text_rect.left - self.button_size_modifier_px, 
            self.text_rect.top - self.button_size_modifier_px, 
            self.text_rect.width + (self.button_size_modifier_px * 2), 
            self.text_rect.height + (self.button_size_modifier_px * 2)
            )
        
        self.highlight_rect = pygame.Rect(
            self.button_rect.left - self.highlight_thickness_px, 
            self.button_rect.top - self.highlight_thickness_px, 
            self.button_rect.width + (self.highlight_thickness_px * 2), 
            self.button_rect.height + (self.highlight_thickness_px * 2)
            )
            
    def is_highlighted(self) -> bool:
        """when mouse is over or this button is the active item without yet being clicked"""
        self.highlighted = False
        if self.button_rect.collidepoint(pygame.mouse.get_pos()):
            self.highlighted = True
            return True

    def draw(self,surface):
        """draws this button on passed surface"""
        if self.highlighted:
            pygame.draw.rect( #draw highlight border rectangle
            surface, self.highlight_colour,
            pygame.Rect(self.highlight_rect))
            
        pygame.draw.rect( #make button bigger rectangle
            surface, self.background_colour,
            pygame.Rect(self.button_rect))
            
        surface.blit(self.button_text, self.text_rect) #overlay the actual text
     
    def selected(self):
        """Checks to see if this button was clicked"""
        for event in pygame.event.get(): # returns list of events and clears queue
            if event.type == pygame.MOUSEBUTTONUP and self.highlighted:
                return True
                     
class Menu:
    """creates a menu consisiting of button objects which can be ordered vertically or horizontally"""
    def __init__(self,order,first_button_loc: Optional[Coordinate] = None,button_spacing_y=50, button_spacing_x=100):
        """ inits a new menu and describes how buttoms are to be layed out
        order:
            vertical = arrange buttons vertical_spacing_px apart
            horizontal = arrange buttons horizontal_spacing_px apart
            explicit = buttons define location when initialized
        """
        
        if order not in ["vertical", "horizontal", "explicit"]:
            raise ValueError('passed order is not of type') 
            
        if (order == "vertical" or order == "horizontal") and first_button_loc == None:
            raise ValueError('first button location must be defined in menu init if using vertical or horizontal ordering')
        
        self.buttons = []
        self.screen = pygame.display.set_mode(GRID_SIZE) #set display size
        
        self.vertical_spacing_px = button_spacing_y
        self.vertical_spacing_next = button_spacing_y
        
        self.horizontal_spacing_px = button_spacing_x
        self.horizontal_spacing_next = button_spacing_x
        
        self.button_order = order
        self.first_button_loc = first_button_loc
        
    def new_button(self,text: str,colour: tuple[int,int,int],location: Optional[Coordinate] = None):
        """ adds new buton object to menu object in horizontal/vertical/explict locations"""
        if self.button_order == "explicit" and location == None:
            raise ValueError('Button location must be defined if menu order is explicit')
            
        if (self.button_order == "vertical" or self.button_order == "horizontal") and location != None:
            raise ValueError('location should not be defined on new_button call if using horizontal or vertical ordering')
        if self.button_order == "vertical":
             location = self.first_button_loc
             self.first_button_loc.y = self.vertical_spacing_next
             self.vertical_spacing_next += self.vertical_spacing_px
        
        if self.button_order == "horizontal":
             location = self.first_button_loc
             self.first_button_loc.x = self.horizontal_spacing_next
             self.horizontal_spacing_next += self.horizontal_spacing_px
         
        self.buttons.append(Button(location,colour,text))
    def show(self):
        self.screen.fill(WHITE)#
        for i in self.buttons:
            i.is_highlighted()
            i.draw(self.screen)
        pygame.display.update()
    def selected_button(self) -> int:
        """ returns index of selected button based on order they were created"""
        for event in pygame.event.get(): # returns list of events and clears queue
            if event.type == pygame.MOUSEBUTTONUP:
                for i,v in enumerate(self.buttons):
                    if v.highlighted:#
                        self.selected_index = i + 1
                        return self.selected_index
        
def menu_how_many_players() -> int:
    """Draws a menu to identify number of players"""
    player_select = Menu("vertical",Coordinate((50,GRID_SIZE[1]/2)))
    player_select.new_button(colour=PINK,text="One player")
    player_select.new_button(colour=PINK,text="Two player")
    player_select.new_button(colour=PINK,text="Quit")
    while True:
        player_select.show() 
        if player_select.selected_button():
            return player_select.selected_index 
    
                    
def game_session(screen: Game_display, players: int) -> int:
    """creates game basd on number of players"""
    game = Game_Logic(players) #initiate game logic object#
    clock = pygame.time.Clock() #init clock
    game.create_food() #generate starting food icons
    pygame.event.clear() #clears events to prevent unexpected direction change at start of game 

    while True: 
        clock.tick(FPS)
        delta = pygame.time.get_ticks() / 1000
        game.read_key_presses(delta)
        game.move_snakes(delta) #snake moves every tick, so update logical list containing segments

        loser = game.check_collisions()
        if loser:  
            if players == 1:
                return loser
            else:
                return game.the_other_player.get(loser)
        
        game.check_food_collision()
        
        screen.show(game) #updates display
        
def main():
    pygame.init()
    pygame.display.set_caption("Snake")
    player_selection = menu_how_many_players()
    if player_selection == 3:
        pygame.quit()
        exit()
    
    try:
        screen = Game_display()
    
        while True:
            winner = game_session(screen,player_selection)
            if player_selection == 1:
                print(f'Score: {winner}')   
            else:
                print(f'{winner} won')           
            
    finally:
        pygame.quit()

if __name__ == '__main__':
    main()
