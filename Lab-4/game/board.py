import random
import pygame
import math

GRID_SIZE = 8
TILE_SIZE = 60
POINTS_PER_GEM = 10
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:

    def __init__(self, color, target_row, col):
        self.color = color
        self.special = None
        self.hint = None
        self.target_row = target_row
        self.col = col
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.hint = None
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y
                self.grid[r][c] = gem

        self.resolve_matches(spawn_specials=False)

    def is_animating(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_runs(self):
            """Return a list of (cells, kind) for every run of 3+ same-colour gems.
            kind is "row" for horizontal runs and "col" for vertical runs."""
            runs = []

            for r in range(GRID_SIZE):
                c = 0
                while c < GRID_SIZE:
                    gem = self.grid[r][c]
                    if gem is None:
                        c += 1
                        continue
                    end = c + 1
                    while (
                        end < GRID_SIZE
                        and self.grid[r][end]
                        and self.grid[r][end].color == gem.color
                    ):
                        end += 1
                    if end - c >= 3:
                        runs.append(([(r, k) for k in range(c, end)], "row"))
                    c = end

            for c in range(GRID_SIZE):
                r = 0
                while r < GRID_SIZE:
                    gem = self.grid[r][c]
                    if gem is None:
                        r += 1
                        continue
                    end = r + 1
                    while (
                        end < GRID_SIZE
                        and self.grid[end][c]
                        and self.grid[end][c].color == gem.color
                    ):
                        end += 1
                    if end - r >= 3:
                        runs.append(([(k, c) for k in range(r, end)], "col"))
                    r = end

            return runs

    def find_matches(self):
        matched = set()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):
                if (
                    self.grid[r][c]
                    and self.grid[r][c + 1]
                    and self.grid[r][c + 2]
                    and self.grid[r][c].color == self.grid[r][c + 1].color == self.grid[r][c + 2].color
                ):
                    matched.update([(r, c), (r, c + 1), (r, c + 2)])

        for r in range(GRID_SIZE - 2):
            for c in range(GRID_SIZE):
                if (
                    self.grid[r][c]
                    and self.grid[r + 1][c]
                    and self.grid[r + 2][c]
                    and self.grid[r][c].color == self.grid[r + 1][c].color == self.grid[r + 2][c].color
                ):
                    matched.update([(r, c), (r + 1, c), (r + 2, c)])

        return matched

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def _pick_spawn_cell(self, cells, swapped):
        """Choose which gem of a 4+ run turns into the special gem."""
        candidates = [p for p in swapped if p in cells]
        candidates.append(cells[len(cells) // 2])
        candidates.extend(cells)
        for r, c in candidates:
            if self.grid[r][c] and not self.grid[r][c].special:
                return (r, c)
        return None

    def _expand_specials(self, cells):
        """Add the full row/column of every special gem in `cells`,
        following chain reactions between special gems."""
        cleared = set(cells)
        queue = [p for p in cleared if self.grid[p[0]][p[1]].special]
        detonated = set()

        while queue:
            r, c = queue.pop()
            if (r, c) in detonated:
                continue
            detonated.add((r, c))
            gem = self.grid[r][c]
            if gem.special == "row":
                line = [(r, k) for k in range(GRID_SIZE)]
            else:
                line = [(k, c) for k in range(GRID_SIZE)]
            for cell in line:
                other = self.grid[cell[0]][cell[1]]
                if other is None:
                    continue
                cleared.add(cell)
                if other.special and cell not in detonated:
                    queue.append(cell)
        return cleared

    def resolve_matches(self,swapped=(), spawn_specials=True):
        total_points = 0
        combo = 0
        while True:
            runs = self.find_runs()
            if not runs:
                break
            combo += 1

            matched = set()
            for cells, _ in runs:
                matched.update(cells)

            spawns = {}
            if spawn_specials:
                for cells, kind in runs:
                    if len(cells) >= 4:
                        cell = self._pick_spawn_cell(
                            cells, swapped if combo == 1 else ()
                        )
                        if cell:
                            spawns[cell] = kind

            to_clear = self._expand_specials(matched)
            for cell in spawns:
                to_clear.discard(cell)

            total_points += len(to_clear) * POINTS_PER_GEM * combo

            for r, c in to_clear:
                self.grid[r][c] = None
            for (r, c), kind in spawns.items():
                self.grid[r][c].special = kind

            self.drop_and_refill()

        self.last_combo = combo
        return total_points

    def find_hint_move(self):
            """Return an adjacent pair whose swap creates a match, or None.
            The board is left unchanged. Only call when no gems are animating."""
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    for dr, dc in ((0, 1), (1, 0)):
                        r2, c2 = r + dr, c + dc
                        if r2 >= GRID_SIZE or c2 >= GRID_SIZE:
                            continue
                        self.swap_gems((r, c), (r2, c2))
                        found = bool(self.find_matches())
                        self.swap_gems((r, c), (r2, c2))   # always undo
                        if found:
                            return ((r, c), (r2, c2))
            return None

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        if not matches:
            self.swap_gems(pos1, pos2)
            return False

        self.moves_remaining -= 1

        self.score += self.resolve_matches(swapped=(pos1, pos2))
        return True

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )
                    if gem.special:
                        pulse = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2
                        glow = (255, int(200 + 55 * pulse), int(100 + 155 * pulse))
                        pygame.draw.rect(surface, glow, tile_rect, width=4, border_radius=10)
                        cx, cy = tile_rect.center
                        if gem.special == "row":
                            pygame.draw.line(surface, glow, (tile_rect.left + 8, cy), (tile_rect.right - 8, cy), 4)
                        else:
                            pygame.draw.line(surface, glow, (cx, tile_rect.top + 8), (cx, tile_rect.bottom - 8), 4)

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )
        if self.hint:
            pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2   # 0..1
            alpha = int(60 + 140 * pulse)
            for r, c in self.hint:
                hx = self.offset_x + c * TILE_SIZE
                hy = self.offset_y + r * TILE_SIZE
                glow = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4), pygame.SRCALPHA)
                pygame.draw.rect(
                    glow, (255, 255, 255, alpha // 2),
                    glow.get_rect(), border_radius=10,
                )
                pygame.draw.rect(
                    glow, (255, 255, 120, alpha),
                    glow.get_rect(), width=4, border_radius=10,
                )
                surface.blit(glow, (hx + 2, hy + 2))
