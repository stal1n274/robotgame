import rg
import random

class Robot:
	def __init__(self):
		""" Init """
		
		self.MAP = []
		self.MAP.append("XXXXXXXXXXXXXXXXXXX")
		self.MAP.append("XXXXXXXOOOOOXXXXXXX")
		self.MAP.append("XXXXXO       OXXXXX")
		self.MAP.append("XXXO           OXXX")
		self.MAP.append("XXX             XXX")
		self.MAP.append("XXO             OXX")
		self.MAP.append("XX               XX")
		self.MAP.append("XO               OX")
		self.MAP.append("XO               OX")
		self.MAP.append("XO               OX")
		self.MAP.append("XO               OX")
		self.MAP.append("XO               OX")
		self.MAP.append("XX               XX")
		self.MAP.append("XXO             OXX")
		self.MAP.append("XXX             XXX")
		self.MAP.append("XXXO           OXXX")
		self.MAP.append("XXXXXO       OXXXXX")
		self.MAP.append("XXXXXXXOOOOOXXXXXXX")
		self.MAP.append("XXXXXXXXXXXXXXXXXXX")

		# Legend:
		# X - wall
		# O - spawn point

		self.RANGE_FRIEND_HELP = 5
		self.RANGE_ENEMY_FOLLOW = 10
		self.HP_CRITICAL_SAVE = 5
		self.LOCS_AROUND_RND = 20

	
	def good_day_to_die(self, game):
		""" Check whether it'd be good to die """
		
		# Get number of nearby robots
		num_enemies = 0
		for loc, bot in game.robots.iteritems():
			if bot.player_id != self.player_id:
				if rg.dist(loc, self.location) <= 1:
					num_enemies = num_enemies + 1
					
		if self.hp < 10 and num_enemies >= 2:
			# it'd be better to die
			print("Enemies: %d, HP: %d" % (num_enemies, self.hp))
			return True
		if self.hp < 31 and num_enemies >= 3:
			# it'd be better to die
			return True

		return False
		
	def move_next(self, destination):
		""" Makes the best move toward to destination """
		
		if self.location == destination:
			# we are in the center
			return ['guard']

		if self.MAP[destination[1]][destination[0]] == 'X':
			# we're trying to move to the wall, find nearest good point
			available_locs = rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn'))
			if len(available_locs) > 0:
				return ['move', available_locs[0]]
			return ['guard']

		return ['move', destination]
		
		
	def get_robots_around(self, location, game):
		""" Return dict of enemy and dict of friend robots with walk distance to certain location """

		enemy_robots_dict = {}
		friend_robots_dict = {}
		for loc, bot in game.robots.iteritems():
			distance = rg.dist(location, loc)
			if bot.player_id != self.player_id:
				# enemy
				# TBD: replace robot with the same wdist only when new HP is lower than in dictionary, otherwise keep
				enemy_robots_dict.update({distance: loc})
			else:
				# friend
				friend_robots_dict.update({distance: loc})
		
		return enemy_robots_dict, friend_robots_dict
		
		
	def act(self, game):
		""" Think globally, act locally """
		
		if self.good_day_to_die(game) is True:
			print("Suicide!")
			return ['suicide']

		if self.hp<self.HP_CRITICAL_SAVE:
			# SOS !!! Run away from enemies
			available_locs = rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn'))
			if len(available_locs) > 0:
				for counter_a in xrange(self.LOCS_AROUND_RND):
					loc = random.choice(available_locs)
					# make sure that next location is free from enemies
					enemies, friends = self.get_robots_around(loc, game)
					if enemies.has_key(1):
						# enemy nearby, find another location
						continue
					else:
						if_spawn_locs_nearby = rg.locs_around(loc, filter_out=('invalid', 'obstacle'))
						if len(if_spawn_locs_nearby) == 0:
							# no ways to move
							break
						for counter_b in xrange(self.LOCS_AROUND_RND):
							if_spawn_loc = random.choice(if_spawn_locs_nearby)
							if 'spawn' in rg.loc_types(if_spawn_loc):
								continue
							else:
								return self.move_next(loc)

		# Check for an enemy around
		enemies = {}
		for loc, bot in game.robots.iteritems():
			if bot.player_id != self.player_id:
				if rg.dist(loc, self.location) <= 1:
					enemies.update({bot.hp: loc})
		if len(enemies) > 0:
			# attack enemy with the lowest HP
			enemies_keys=enemies.keys()
			enemies_keys.sort()
			return ['attack', enemies[enemies_keys[0]]]

		# No enemies in 1 step, check whether there any friend nearby who needs help
		enemies, friends = self.get_robots_around(self.location, game)
		friends_keys = friends.keys()
		friends_keys.sort()
		for key in friends_keys:
			# key is a wdist
			if key>self.RANGE_FRIEND_HELP:
				# friends are out of range
				break
			
			# check whether our friend attacks enemy
			f_enemies, f_friends = self.get_robots_around(friends[key], game)

			if f_enemies.has_key(1):
				# friend attacks enemy, get nearby point to walk
				available_locs = rg.locs_around(f_enemies[1], filter_out=('invalid', 'obstacle'))
				for loc in available_locs:
					if loc not in game.robots:
						return self.move_next(rg.toward(self.location, loc))
				# try to move directly to the center, TBD: this is bad decision, we'd need to modify this behavior
				return self.move_next(rg.toward(self.location, rg.CENTER_POINT))

			if f_enemies.has_key(2):
				# friend has a candidate for attack, join him
				available_locs = rg.locs_around(f_enemies[2], filter_out=('invalid', 'obstacle'))
				for loc in available_locs:
					if loc not in game.robots:
						return self.move_next(rg.toward(self.location, loc))
				# try to move directly to the center, TBD: this is bad decision, we'd need to modify this behavior
				return self.move_next(rg.toward(self.location, rg.CENTER_POINT))

		# follow nearby enemy
		enemies_keys = enemies.keys()
		enemies_keys.sort()
		for key in enemies_keys:
			# key is a wdist
			if key>self.RANGE_ENEMY_FOLLOW:
				# no enemies nearby
				break

			available_locs = rg.locs_around(enemies[key], filter_out=('invalid', 'obstacle'))
			for loc in available_locs:
				if loc not in game.robots:
					return self.move_next(rg.toward(self.location, loc))
			# try to move directly to the center, TBD: this is bad decision, we'd need to modify this behavior
			return self.move_next(rg.toward(self.location, rg.CENTER_POINT))
			
		# nothing to do, lets move to the center
		return self.move_next(rg.toward(self.location, rg.CENTER_POINT))


		