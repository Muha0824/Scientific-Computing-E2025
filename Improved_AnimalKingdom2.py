import pygame, random
import numpy as np

col_new_fish = (0, 128, 255)
col_young_fish = (15,82,186)
col_breeding_fish = (0, 255, 255)

col_new_bear = (150,75,0)
col_young_bear = (165,113,78)
col_breeding_bear = (150,75,0)
col_starving_bear = (75,75,75)

col_empty = (213, 196, 161)
col_grid = (30, 30, 60)

# Plant colors added (different growth stages)
col_small_plant = (34, 139, 34)     # green - young plant
col_growing_plant = (0, 200, 0)     # lighter green
col_mature_plant = (173, 255, 47)   # yellow-green (mature)

FRAMES_PER_SECOND = 60
SPEED = 15

ID = 0
def new_ID():
    global ID
    currentID = ID
    ID += 1
    return currentID

# OPTIMIZED PARAMETERS FOR LONG-TERM STABILITY
fish_breed_age = 10           # Balanced breeding speed
fish_overcrowd = 6            # Very tolerant of neighbors
fish_starvation = 15          # Good survival time
fish_energy_cost = 2          # Moderate breeding cost

def new_fish():
    ID_fish = new_ID()
    fish = {'type': 'fish', 'id':ID_fish, 'col':col_new_fish, 'age': 0, 'food': fish_starvation}
    return fish

# Bear parameters
bear_breed_age = 15           # Slower breeding for predators
bear_starvation = 25          # Very long survival time
bear_overcrowd = 5            # Tolerant of neighbors
bear_energy_cost = 3          # Moderate breeding cost

def new_bear():
    ID_bear = new_ID()
    bear = {'type': 'bear', 'id':ID_bear, 'age': 0, 'col':col_new_bear, 'food': bear_starvation}
    return bear

# Plant parameters
plant_growth_time = 4          # Balanced growth
plant_max_age = 15            # Reasonable lifespan
plant_breed_chance = 0.35     # Sustainable reproduction rate
plant_max_density = 6         # Prevents overpopulation but allows spread

def new_plant():
    ID_plant = new_ID()
    plant = {'type': 'plant', 'id': ID_plant, 'age': 0, 'col': col_small_plant}
    return plant

def empty():
    return {'type': 'empty'}

def init(dimx, dimy, fish, bear, plant):
    content_list = []
    for i in range(fish):
        content_list.append(new_fish())
    for i in range(bear):
        content_list.append(new_bear())
    for i in range(plant):
        content_list.append(new_plant())
    for i in range((dimx * dimy - fish - bear - plant)):
        content_list.append(empty())

    random.shuffle(content_list)
    cells_array = np.array(content_list)
    cells = np.reshape(cells_array, (dimy, dimx))
    return cells

def get_neighbors(cur, r, c):
    r_min, c_min = 0 , 0
    r_max, c_max = cur.shape
    r_max, c_max = r_max -1 , c_max-1
    neighbours = []
    if r-1 >= r_min :
        if c-1 >= c_min: neighbours.append((r-1,c-1))
        neighbours.append((r-1,c))
        if c+1 <= c_max: neighbours.append((r - 1, c+1))
    if c-1 >= c_min: neighbours.append((r,c-1))
    if c + 1 <= c_max: neighbours.append((r,c+1))
    if r + 1 <= r_max:
        if c - 1 >= c_min: neighbours.append((r+1,c-1))
        neighbours.append((r+1, c))
        if c + 1 <= c_max: neighbours.append((r+1,c+1))
    return neighbours

def neighbour_fish_plant_empty_rest(cur,neighbours):
    fish_neighbours =[]
    plant_neighbours = []
    empty_neighbours =[]
    rest_neighbours=[]

    for neighbour in neighbours:
        cell = cur[neighbour]
        if cell['type'] == "fish":
            fish_neighbours.append(neighbour)
        elif cell['type'] == "plant":
            plant_neighbours.append(neighbour)
        elif cell['type'] == "empty":
            empty_neighbours.append(neighbour)
        else:
            rest_neighbours.append(neighbour)

    return fish_neighbours, plant_neighbours, empty_neighbours

def fish_rules(cur,r,c,neighbour_fish, neighbour_plant, neighbour_empty):
    """IMPROVED: Better energy management and movement"""
    cur[r,c]['age'] += 1
    
    # ENERGY MANAGEMENT - Only consume food when moving/breeding
    if len(neighbour_empty) > 0 or len(neighbour_plant) > 0:
        cur[r,c]['food'] -= 1

    # FISH EAT PLANTS - Smart eating behavior
    if len(neighbour_plant) > 0:
        if cur[r,c]['food'] < fish_starvation * 0.6:  # Eat when moderately hungry
            r_plant, c_plant = random.choice(neighbour_plant)
            cur[r_plant, c_plant] = empty()
            cur[r,c]['food'] = min(fish_starvation, cur[r,c]['food'] + 8)  # Partial refill
            neighbour_plant.remove((r_plant, c_plant))
            neighbour_empty.append((r_plant, c_plant))

    # Starvation death
    if cur[r,c]['food'] <= 0:
        cur[r, c] = empty()
        return cur

    # Breeding - energy-based with cooldown
    if (cur[r,c]['age'] >= fish_breed_age and 
        cur[r,c]['food'] > fish_starvation * 0.6 and
        len(neighbour_empty) > 0):
        
        cur[r,c]['col'] = col_breeding_fish
        r_empty, c_empty = random.choice(neighbour_empty)
        cur[r_empty, c_empty] = new_fish()
        cur[r, c]['age'] = 0
        cur[r, c]['food'] -= fish_energy_cost
        cur[r, c]['col'] = col_young_fish  # Reset color after breeding

    # Overcrowding death - very rare and density-based
    elif len(neighbour_fish) >= fish_overcrowd:
        # Only die if extremely crowded AND low on food
        if (len(neighbour_fish) >= fish_overcrowd + 2 and 
            cur[r,c]['food'] < fish_starvation * 0.3 and
            random.random() < 0.3):
            cur[r, c] = empty()
            return cur

    # Movement - energy efficient
    if len(neighbour_empty) > 0:
        # Prefer moving toward plants if hungry
        target_cells = []
        if cur[r,c]['food'] < fish_starvation * 0.7:
            # Look for empty cells adjacent to plants
            for empty_pos in neighbour_empty:
                empty_neighbors = get_neighbors(cur, empty_pos[0], empty_pos[1])
                for en_r, en_c in empty_neighbors:
                    if cur[en_r, en_c]['type'] == 'plant':
                        target_cells.append(empty_pos)
                        break
        
        if not target_cells:
            target_cells = neighbour_empty
            
        r_new, c_new = random.choice(target_cells)
        cur[r_new, c_new] = cur[r,c]
        cur[r,c] = empty()

    return cur

def bear_rules(cur,r,c,neighbour_fish, neighbour_empty):
    """IMPROVED: Better hunting and energy conservation"""
    cur[r, c]['age'] += 1

    # Update colors
    if cur[r, c]['age'] >= bear_breed_age:
        cur[r, c]['col'] = col_breeding_bear
    else:
        cur[r, c]['col'] = col_young_bear

    if cur[r, c]['food'] <= 8:  # Show starving earlier for better feedback
        cur[r, c]['col'] = col_starving_bear

    # Count bear neighbors for social behavior
    all_neighbors = get_neighbors(cur, r, c)
    bear_neighbors = sum(1 for nr, nc in all_neighbors if cur[nr, nc]['type'] == 'bear')

    # Eating logic - bears eat fish with energy gain
    if len(neighbour_fish) > 0:
        # More fish = more energy gain
        fish_eaten = min(2, len(neighbour_fish))  # Can eat up to 2 fish
        for _ in range(fish_eaten):
            if neighbour_fish:  # Check if list is not empty
                r_fish, c_fish = random.choice(neighbour_fish)
                cur[r_fish, c_fish] = empty()
                neighbour_fish.remove((r_fish, c_fish))
                neighbour_empty.append((r_fish, c_fish))
        
        cur[r, c]['food'] = bear_starvation  # Full refill when eating
        
    else:
        # Slower starvation - conserve energy when not hunting
        if random.random() < 0.7:  # Only lose food 70% of time
            cur[r, c]['food'] -= 1

    # Death conditions - very forgiving
    if cur[r, c]['food'] <= 0:
        cur[r, c] = empty()
        return cur
    
    # Overcrowding death - only in extreme cases
    if bear_neighbors >= bear_overcrowd + 2 and random.random() < 0.2:
        cur[r, c] = empty()
        return cur

    # Breeding logic - sustainable requirements
    food_requirement = bear_starvation * 0.5
    if (cur[r, c]['age'] >= bear_breed_age and 
        len(neighbour_empty) > 0 and 
        cur[r, c]['food'] > food_requirement and
        bear_neighbors < 3):  # Prefer some isolation for breeding
        
        r_new, c_new = random.choice(neighbour_empty)
        cur[r_new, c_new] = new_bear()
        cur[r, c]['age'] = 0
        cur[r, c]['food'] -= bear_energy_cost
        cur[r, c]['col'] = col_young_bear  # Reset color

    # Movement - strategic hunting
    elif len(neighbour_empty) > 0:
        # Hunt for fish if hungry
        target_cells = []
        if cur[r, c]['food'] < bear_starvation * 0.6:
            # Look for empty cells adjacent to fish
            for empty_pos in neighbour_empty:
                empty_neighbors = get_neighbors(cur, empty_pos[0], empty_pos[1])
                for en_r, en_c in empty_neighbors:
                    if cur[en_r, en_c]['type'] == 'fish':
                        target_cells.append(empty_pos)
                        break
        
        if not target_cells:
            target_cells = neighbour_empty
            
        r_new, c_new = random.choice(target_cells)
        cur[r_new, c_new] = cur[r, c]
        cur[r, c] = empty()
            
    return cur

def plant_rules(cur, r, c, neighbour_empty):
    """IMPROVED: Sustainable growth with environmental adaptation"""
    cur[r, c]['age'] += 1
    age = cur[r, c]['age']

    # Growth stages with color coding
    if age < plant_growth_time:
        cur[r, c]['col'] = col_small_plant
    elif age < plant_growth_time * 2:
        cur[r, c]['col'] = col_growing_plant
    elif age < plant_max_age:
        cur[r, c]['col'] = col_mature_plant
    else:
        # Graceful aging - chance to survive longer
        survival_chance = 0.4 if len(neighbour_empty) > 2 else 0.1
        if random.random() < survival_chance:
            cur[r, c]['age'] = plant_max_age - random.randint(1, 3)
        else:
            cur[r, c] = empty()
        return cur

    # ADAPTIVE REPRODUCTION BASED ON ENVIRONMENT
    all_neighbors = get_neighbors(cur, r, c)
    plant_count = sum(1 for nr, nc in all_neighbors if cur[nr, nc]['type'] == 'plant')
    empty_count = len(neighbour_empty)
    
    # Dynamic reproduction chance based on local conditions
    actual_breed_chance = plant_breed_chance
    if plant_count > plant_max_density:
        actual_breed_chance *= 0.3  # Reduce reproduction in dense areas
    elif empty_count > 5:
        actual_breed_chance *= 1.2  # Increase in open areas
    
    # Reproduce if conditions are good
    if (age >= plant_growth_time * 2 and 
        random.random() < actual_breed_chance and 
        len(neighbour_empty) > 0 and
        plant_count <= plant_max_density):
        
        r_new, c_new = random.choice(neighbour_empty)
        cur[r_new, c_new] = new_plant()

    return cur

def update(surface, cur, sz):
    # Track populations for monitoring
    fish_count = 0
    bear_count = 0
    plant_count = 0
    empty_count = 0
    
    # Count populations first
    for r, c in np.ndindex(cur.shape):
        if cur[r, c]['type'] == "fish":
            fish_count += 1
        elif cur[r, c]['type'] == "bear":
            bear_count += 1
        elif cur[r, c]['type'] == "plant":
            plant_count += 1
        else:
            empty_count += 1
    
    # Ecosystem health monitoring
    total_cells = fish_count + bear_count + plant_count + empty_count
    health_indicator = "HEALTHY"
    if plant_count < total_cells * 0.1:
        health_indicator = "LOW PLANTS"
    elif fish_count < 5:
        health_indicator = "LOW FISH"
    elif bear_count < 2:
        health_indicator = "LOW BEARS"
    
    print(f"Populations - Fish: {fish_count}, Bears: {bear_count}, Plants: {plant_count}, Empty: {empty_count} [{health_indicator}]")
    
    # Update each cell
    for r, c in np.ndindex(cur.shape):
        if cur[r, c]['type'] == "fish" or cur[r, c]['type'] == "bear" or cur[r, c]['type'] == "plant":
            neighbours = get_neighbors(cur, r, c)
            neighbour_fish, neighbour_plant, neighbour_empty = neighbour_fish_plant_empty_rest(cur, neighbours)
            
            if cur[r, c]['type'] == "fish":
                cur = fish_rules(cur, r, c, neighbour_fish, neighbour_plant, neighbour_empty)
            elif cur[r, c]['type'] == "bear":
                cur = bear_rules(cur, r, c, neighbour_fish, neighbour_empty)
            elif cur[r, c]['type'] == "plant":
                cur = plant_rules(cur, r, c, neighbour_empty)
    return cur

def draw_grid(surface,cur,sz):
    for r, c in np.ndindex(cur.shape):
        col = col_empty
        if cur[r, c]['type'] != 'empty':
            col = cur[r, c]['col']
        pygame.draw.rect(surface, col, (c * sz, r * sz, sz - 1, sz - 1))

def main(dimx, dimy, cellsize, fish, bear, plant):
    pygame.init()
    surface = pygame.display.set_mode((dimx * cellsize, dimy * cellsize))
    pygame.display.set_caption("Animal Kingdom - SUSTAINABLE ECOSYSTEM")

    cells = init(dimx, dimy, fish, bear, plant)

    clock = pygame.time.Clock()
    speed_count = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        surface.fill(col_grid)
        if(speed_count % SPEED == 0):
            print(f"timestep: {speed_count // SPEED}")
            cells = update(surface, cells, cellsize)
        draw_grid(surface, cells, cellsize)
        pygame.display.update()
        clock.tick(FRAMES_PER_SECOND)
        speed_count = speed_count + 1

if __name__ == "__main__":
    # OPTIMIZED STARTING POPULATIONS FOR LONG-TERM STABILITY
    fish = 25    # Sustainable fish population
    bear = 6     # Fewer predators for balance
    plant = 80   # Strong plant base
    main(50, 20, 16, fish, bear, plant)