import pygame as pg
import neat
import time
import os
import random

pg.font.init() # init pygame fonts
GEN = 0
# constants
WIN_WIDTH = 500
WIND_HEIGHT = 800

# load imgs
BIRD_IMGS = [
  pg.transform.scale2x(pg.image.load(os.path.join('NEAT/imgs','bird1.png'))),
  pg.transform.scale2x(pg.image.load(os.path.join('NEAT/imgs','bird2.png'))),
  pg.transform.scale2x(pg.image.load(os.path.join('NEAT/imgs','bird3.png')))
  ]

PIPE_IMG = pg.transform.scale2x(pg.image.load(os.path.join('NEAT/imgs','pipe.png')))
BASE_IMG = pg.transform.scale2x(pg.image.load(os.path.join('NEAT/imgs','base.png')))
BG_IMG = pg.transform.scale2x(pg.image.load(os.path.join('NEAT/imgs','bg.png')))
PIPE_FREQ = 600
STAT_FONT = pg.font.SysFont("comicsans", 50)

class Bird:
  IMGS = BIRD_IMGS
  MAX_ROT = 25 # tilt bird
  ROT_VEL = 20
  ANIMATION_TIME = 5 # how fast bird flap wings

  def __init__(self, x, y):
    # init pos
    self.x = x
    self.y = y
    self.tilt = 0
    self.tick_cnt = 0
    self.vel = 0
    self.height = self.y
    self.img_cnt = 0
    self.img = self.IMGS[0]

  def jump(self):
    self.vel = -10.5 # top-left is (0,0) right: +x, down: +y
    self.tick_cnt = 0 
    self.height = self.y # where the bird start moving

  def move(self):
    self.tick_cnt += 1
    # how many pixels when jump per frame # physics!
    d = self.vel*self.tick_cnt + 1.5*self.tick_cnt**2

    # terminal velocity
    if d >= 16:
      d = 16
    if d < 0:
      d -= 2

    self.y = self.y + d

    # when starting tilting bird downward
    if d < 0 or self.y < self.height + 50:
      if self.tilt < self.MAX_ROT:
        self.tilt = self.MAX_ROT
    else:
      if self.tilt > -90:
        self.tilt -= self.ROT_VEL
    
  def draw(self, win):
    self.img_cnt += 1

    # what imgs should we pick based on the img count
    # flapping wings
    if self.img_cnt < self.ANIMATION_TIME:
      self.img = self.IMGS[0]
    elif self.img_cnt < self.ANIMATION_TIME*2:
      self.img = self.IMGS[1]
    elif self.img_cnt < self.ANIMATION_TIME*3:
      self.img = self.IMGS[2]
    elif self.img_cnt < self.ANIMATION_TIME*4:
      self.img = self.IMGS[1]
    elif self.img_cnt == self.ANIMATION_TIME*4 + 1:
      self.img = self.IMGS[0]
      self.img_cnt = 0
    
    # when dropping no wing flapping
    if self.tilt <= -80:
      self.img = self.IMGS[1]
      self.img_cnt = self.ANIMATION_TIME*2
    
    # rot the img around center
    rotated_img = pg.transform.rotate(self.img, self.tilt)
    new_rect = rotated_img.get_rect(
      center = self.img.get_rect(
        topleft = (self.x, self.y)
        ).center)
    win.blit(rotated_img, new_rect.topleft)

  # the real pixels array of the object bounding box
  def get_mask(self):
    return pg.mask.from_surface(self.img)

class Pipe:
  GAP = 200
  VEL = 5

  # only def x since y will be set random
  def __init__(self, x):
    self.x = x
    self.height = 0
    self.gap = 100

    # keep track where the pipe would be drawn
    self.top = 0
    self.bottom = 0
    self.PIPE_TOP = pg.transform.flip(PIPE_IMG, False, True)
    self.PIPE_BOTTOM = PIPE_IMG

    # if bird pass the pipe, and for collision favor
    self.passed = False
    self.set_height()
  
  def set_height(self):
    self.height = random.randrange(50,450)
    self.top = self.height - self.PIPE_TOP.get_height()
    self.bottom = self.height + self.GAP
  
  def move(self):
    self.x -= self.VEL
  
  def draw(self, win):
    win.blit(self.PIPE_TOP, (self.x, self.top))
    win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

  def collide(self, bird):
    bird_mask = bird.get_mask()
    top_mask = pg.mask.from_surface(self.PIPE_TOP)
    bottom_mask = pg.mask.from_surface(self.PIPE_BOTTOM)
  
    top_offset = (self.x - bird.x, self.top - round(bird.y))
    bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

    # if pixels are overlapping
    b_point = bird_mask.overlap(bottom_mask, bottom_offset)
    t_point = bird_mask.overlap(top_mask, top_offset)

    if t_point or b_point:
      return True
    return False
  
class Base:
  VEL = 5 # same with the pipe velocity
  WIDTH = BASE_IMG.get_width()
  IMG = BASE_IMG

  def __init__(self, y):
    self.y = y
    self.x1 = 0
    self.x2 = self.WIDTH
  
  # two base img move
  # if one piece of base img is completely out of screen,
  # then it will be reset to the right-upcoming place.
  def move(self):
    self.x1 -= self.VEL
    self.x2 -= self.VEL

    if self.x1 + self.WIDTH < 0:
      self.x1 = self.x2 + self.WIDTH

    if self.x2 + self.WIDTH < 0:
      self.x2 = self.x1 + self.WIDTH

  def draw(self, win):
    win.blit(self.IMG, (self.x1, self.y))
    win.blit(self.IMG, (self.x2, self.y))

# draw background img
def draw_window(win, birds, pipes, base, score, gen):
  win.blit(BG_IMG, (0,0))

  for pipe in pipes:
    pipe.draw(win)

  text = STAT_FONT.render("Score: "+str(score), 1, (255,255,255), None)
  win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

  text = STAT_FONT.render("Gen: "+str(gen), 1, (255,255,255), None)
  win.blit(text, (10, 10))

  base.draw(win)
  for bird in birds:
    bird.draw(win)
  pg.display.update()

# main loop of game
# fitness function of neat
def main(genomes, config):
  global GEN
  GEN += 1
  # keep track neurals
  nets = []
  ge = []
  birds = []

  for _, g in genomes: # genomes return tuple of (id, genome obj)
    net = neat.nn.FeedForwardNetwork.create(g, config)
    nets.append(net)
    birds.append(Bird(x = 230, y = 350))
    g.fitness = 0
    ge.append(g)
  # bird = Bird(x = 230, y = 350)
  base = Base(y = 730)
  pipes = [Pipe(x = PIPE_FREQ)] # if x is smaller, pipe generates faster
  win = pg.display.set_mode((WIN_WIDTH, WIND_HEIGHT))
  clock = pg.time.Clock() # set dps
  score = 0
  run = True
  while run:
    clock.tick(60) # set dps
    # game listener
    for event in pg.event.get():
      # if close the win via 'X' at top-right of window
      if event.type == pg.QUIT:
        run = False
        pg.quit()
        quit()
    
    # inputs for the neural network
    pipe_idx = 0 
    if len(birds) > 0:
      # if pass a pipe, set index to new pipe
      if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
        pipe_idx = 1
    else: # if no birds left
      run = False
      break
    # pass inputs values to neural network
    for x, bird in enumerate(birds):
      bird.move()
      ge[x].fitness += 0.1 # encourage bird alive

      output = nets[x].activate((bird.y,
                                 abs(bird.y-pipes[pipe_idx].height),
                                 abs(bird.y - pipes[pipe_idx].bottom)))
      # in this case, the output is only one value
      if output[0] > 0.5:
        bird.jump()

    # bird.move()
    rem = [] # removee
    add_pipe = False
    for pipe in pipes:
      for x, bird in enumerate(birds):
        # remove dead bird
        if pipe.collide(bird):
          ge[x].fitness -= 1 # encourage not hit pipe
          birds.pop(x)
          nets.pop(x)
          ge.pop(x)
        # if bird passed the pipe, generator another pipe
        if not pipe.passed and pipe.x < bird.x:
          pipe.passed = True
          add_pipe = True

      # if pipe is completely off-screen
      if pipe.x + pipe.PIPE_TOP.get_width() < 0:
        rem.append(pipe)

      pipe.move()
    if add_pipe:
      score += 1
      for g in ge:
        g.fitness += 5
      pipes.append(Pipe(x = PIPE_FREQ)) # if x is smaller, pipe generates faster

    for r in rem:
      pipes.remove(r)

    # if bird hits the ground or jump beyond top,
    # then remove such bird
    for x, bird in enumerate(birds):
      if bird.y + bird.img.get_width() >= 730 or bird.y < 0:
        birds.pop(x)
        nets.pop(x)
        ge.pop(x)

    # end point, threshold for the most powerful network
    if score  > 50:
      break

    base.move()
    draw_window(win, birds, pipes,
                base, score, GEN)


def run(config_path):
  # config parser
  config = neat.config.Config(neat.DefaultGenome,
                              neat.DefaultReproduction,
                              neat.DefaultSpeciesSet,
                              neat.DefaultStagnation,
                              config_path)
  p = neat.Population(config) # population
  p.add_reporter(neat.StdOutReporter(True))
  stats = neat.StatisticsReporter()
  p.add_reporter(stats)

  winner = p.run(main, 50)
  # winner.save # to save the most powerful neural network
                # one way to save is to use pickle.


if __name__ == "__main__":
  local_dir = os.path.dirname(__file__)
  config_path = os.path.join(local_dir, "config.txt")
  run(config_path)