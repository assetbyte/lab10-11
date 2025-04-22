import pygame, sys, random, time, psycopg2

def connect_db():
    return psycopg2.connect(
        dbname="snake_game",
        user="postgres",
        password="8554",
        host="localhost",
        port="5432"
    )

def get_or_create_user(username):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if user:
        user_id = user[0]
    else:
        cur.execute("INSERT INTO users (username) VALUES (%s) RETURNING id", (username,))
        user_id = cur.fetchone()[0]
        conn.commit()
    cur.close()
    conn.close()
    return user_id

def get_user_score(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT score, level FROM user_score WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result if result else (0, 1)

def save_game_state(user_id, score, level, snake_pos):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_score (user_id, score, level, state) VALUES (%s, %s, %s, %s)",
        (user_id, score, level, str(snake_pos))
    )
    conn.commit()
    cur.close()
    conn.close()

pygame.init()
WIDTH, HEIGHT = 600, 600
BLOCK_SIZE = 50
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
font = pygame.font.Font(None, 36)


username = input("Enter your username: ")
user_id = get_or_create_user(username)
score, level = get_user_score(user_id)
print(f"Welcome back, {username}! Current level: {level}")


clock = pygame.time.Clock()
if level == 1:
    clock_speed = 7
elif level == 2:
    clock_speed = 10
else:
    clock_speed = 12

class Snake:
    def __init__(self):
        self.x, self.y = BLOCK_SIZE, BLOCK_SIZE
        self.xdir = 1
        self.ydir = 0
        self.head = pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
        self.body = [pygame.Rect(self.x - BLOCK_SIZE, self.y, BLOCK_SIZE, BLOCK_SIZE)]
        self.dead = False

    def update(self):
        global apples, score
        for square in self.body:
            if self.head.x == square.x and self.head.y == square.y:
                self.dead = True
        if self.head.x not in range(0, WIDTH) or self.head.y not in range(0, HEIGHT):
            self.dead = True

        self.body.append(pygame.Rect(self.head.x, self.head.y, BLOCK_SIZE, BLOCK_SIZE))
        self.head.x += self.xdir * BLOCK_SIZE
        self.head.y += self.ydir * BLOCK_SIZE
        self.body.pop(0)

class Apple:
    def __init__(self):
        self.x = random.randint(0, WIDTH // BLOCK_SIZE - 1) * BLOCK_SIZE
        self.y = random.randint(0, HEIGHT // BLOCK_SIZE - 1) * BLOCK_SIZE
        self.weight = random.choice([1, 2, 3])
        self.spawn_time = time.time()
        self.rect = pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
        if self.weight == 1:
            self.color = "red"
        elif self.weight == 2:
            self.color = "orange"
        else:
            self.color = "yellow"

    def update(self):
        pygame.draw.rect(screen, self.color, self.rect)

def draw_area():
    for x in range(0, WIDTH, BLOCK_SIZE):
        for y in range(0, HEIGHT, BLOCK_SIZE):
            pygame.draw.rect(screen, "gray", (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_score():
    text = font.render(f"Score: {score}", True, "white")
    screen.blit(text, (10, 10))

def play_sound():
    try:
        pygame.mixer.music.load("snake/Eating.mp3")
        pygame.mixer.music.play()
    except:
        pass

def draw_menu(score_to_show=None):
    screen.fill("black")
    title = font.render("Snake Game", True, "white")
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))

    if score_to_show is not None:
        score_text = font.render(f"Your Score: {score_to_show}", True, "white")
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 60))

    play_button = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2, 120, 40)
    pygame.draw.rect(screen, "green", play_button)
    play_text = font.render("Play", True, "black")
    screen.blit(play_text, (play_button.x + 25, play_button.y + 5))

    pygame.display.update()
    return play_button

def level_up():
    global level, clock_speed
    if score >= 10 * level:  
        level += 1
        if level == 2:
            clock_speed = 10
        elif level == 3:
            clock_speed = 12
        print(f"Level Up! New Level: {level}")

def game_loop():
    global score, apples
    snake = Snake()
    apples = [Apple()]
    score = 0

    while True:
        screen.fill("black")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN and snake.ydir != -1:
                    snake.ydir = 1
                    snake.xdir = 0
                elif event.key == pygame.K_UP and snake.ydir != 1:
                    snake.ydir = -1
                    snake.xdir = 0
                elif event.key == pygame.K_RIGHT and snake.xdir != -1:
                    snake.ydir = 0
                    snake.xdir = 1
                elif event.key == pygame.K_LEFT and snake.xdir != 1:
                    snake.ydir = 0
                    snake.xdir = -1
                elif event.key == pygame.K_p:
                    snake_pos = [(snake.head.x, snake.head.y)] + [(s.x, s.y) for s in snake.body]
                    save_game_state(user_id, score, level, snake_pos)
                    paused = True
                    print("Game paused. Press P to resume.")
                    while paused:
                        for e in pygame.event.get():
                            if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                                paused = False
                                print("Game resumed.")

        snake.update()

        if snake.dead:
            snake_pos = [(snake.head.x, snake.head.y)] + [(s.x, s.y) for s in snake.body]
            save_game_state(user_id, score, level, snake_pos)
            return  # выход из game_loop, вернёмся в меню

        level_up()  # проверка на повышение уровня

        draw_area()

        for a in apples:
            a.update()
            if snake.head.colliderect(a.rect):
                play_sound()
                score += a.weight
                tail = snake.body[0]
                snake.body.insert(0, pygame.Rect(tail.x, tail.y, BLOCK_SIZE, BLOCK_SIZE))
                apples.remove(a)
                break

        current_time = time.time()
        apples = [a for a in apples if current_time - a.spawn_time < 5]

        if len(apples) == 0:
            apples.append(Apple())

        pygame.draw.rect(screen, "green", snake.head)
        for segment in snake.body:
            pygame.draw.rect(screen, "green", segment)

        draw_score()
        pygame.display.update()
        clock.tick(clock_speed)


while True:
    play_button = draw_menu(score)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    waiting = False 
    game_loop()
