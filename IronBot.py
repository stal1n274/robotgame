import rg

class Robot:
	def __init__(self):
		""" define all interested spawn points (X, Y)

		0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8
		1 X X X X X X O O O O O X X X X X X X
		2 X X X X O o           o O X X X X X
		3 X X O o                   o O X X X
		4 X X o                       o X X X
		5 X O                           O X X
		6 X o                           o X X
		7 O                               O X
		8 O                               O X
		9 O                               O X
		0 O                               O X
		1 O                               O X
		2 X o                           o X X
		3 X O                           O X X
		4 X X o                       o X X X
		5 X X O o                   o O X X X
		6 X X X X O o           o O X X X X X
		7 X X X X X X O O O O O X X X X X X X
		8 X X X X X X X X X X X X X X X X X X

		Legend:
		X - wall
		O - uninteresting spawn points
		o - interesting spawn points
		"""
		
		# Upper-Left corner
		self.SPAWN_SPOTS_OF_INTEREST = ((3, 7), (4, 6), (5, 4), (6, 5), (5, 5), (7, 3), (7, 4))
		# Bottom-Left corner
		self.SPAWN_SPOTS_OF_INTEREST = self.SPAWN_SPOTS_OF_INTEREST + ((11, 3), (12, 4), (13, 4), (14, 5), (14, 6), (15, 7), (15, 8))
		# Upper-Right corner
		self.SPAWN_SPOTS_OF_INTEREST = self.SPAWN_SPOTS_OF_INTEREST + ((3, 11), (4, 12), (4, 13), (5, 14), (6, 14), (7, 15), (8, 15))
		# Bottom-Right corner
		self.SPAWN_SPOTS_OF_INTEREST = self.SPAWN_SPOTS_OF_INTEREST + ((15, 11), (14, 12), (14, 13), (13, 14), (12, 14), (11, 15), (11, 15))

		# Spots to reach:
		# Upper-Left corner
		#self.SPAWN_SPOTS_OF_INTEREST = ((2, 7), (3, 6), (3, 5), (4, 4), (5, 3), (6, 3), (7, 2))
		# Upper-Right corner
		#self.SPAWN_SPOTS_OF_INTEREST = self.SPAWN_SPOTS_OF_INTEREST + ((11, 2), (12, 3), (13, 3), (14, 4), (15, 5), (15, 6), (16, 7))
		# Bottom-Left corner
		#self.SPAWN_SPOTS_OF_INTEREST = self.SPAWN_SPOTS_OF_INTEREST + ((2, 11), (3, 12), (3, 13), (4, 14), (5, 15), (6, 15), (7, 16))
		# Bottom-Right corner
		#self.SPAWN_SPOTS_OF_INTEREST = self.SPAWN_SPOTS_OF_INTEREST + ((16, 11), (15, 12), (15, 13), (14, 14), (13, 15), (12, 15), (11, 16))

		self.RANGE_FRIEND_HELP = 20
		self.RANGE_ENEMY_FOLLOW = 3
		

	def get_robots_around(self, location, game):
		""" Return dict of enemy and dict of friend robots with walk distance to certain location """

		enemy_robots_dict = {}
		friend_robots_dict = {}
		for loc, bot in game.robots.iteritems():
			distance = rg.wdist(self.location, loc)
			if bot.player_id != self.player_id:
				# enemy
				# TBD: replace robot with the same wdist only when new HP is lower than in dictionary
				enemy_robots_dict.update({distance: loc})
			else:
				# friend
				friend_robots_dict.update({distance: loc})
		
		return enemy_robots_dict, friend_robots_dict
		
		
	def act(self, game):
		""" Think globally, act locally """
		
		own_location = self.location

		if own_location in self.SPAWN_SPOTS_OF_INTEREST:
			# Check for an enemy around
			for loc, bot in game.robots.iteritems():
				if bot.player_id != self.player_id:
					if rg.dist(loc, self.location) <= 1:
						return ['attack', loc]
			
			# No enemies in 1 step, check whether there any friend nearby who needs help
			enemies, friends = self.get_robots_around(own_location, game)
			friends_keys = friends.keys()
			friends_keys.sort()
			for key in friends_keys:
				# key is a wdist
				if key>self.RANGE_FRIEND_HELP:
					# other friends are out of range
					break
				
				# check whether our friend attacks enemy
				f_enemies, f_friends = self.get_robots_around(friends[key], game)

				if f_enemies.has_key(1):
					# friend attacks enemy, get nearby point to walk
					available_locs = rg.locs_around(f_enemies[1], filter_out=(['invalid', 'obstacle']))
					for loc in available_locs:
						if loc not in game.robots:
							return ['move', rg.toward(own_location, available_locs[0])]
					# try to move directly to the center, TBD: this is bad decision, we'd need to modify this behavior
					return ['move', rg.toward(self.location, rg.CENTER_POINT)]

				if f_enemies.has_key(2):
					# friend has a candidate for attack, join him
					available_locs = rg.locs_around(f_enemies[2], filter_out=(['invalid', 'obstacle']))
					for loc in available_locs:
						if loc not in game.robots:
							return ['move', rg.toward(own_location, available_locs[0])]
					# try to move directly to the center, TBD: this is bad decision, we'd need to modify this behavior
					return ['move', rg.toward(self.location, rg.CENTER_POINT)]


			
			# stub
			return ['guard']
		else:
			# Check for an enemy around
			for loc, bot in game.robots.iteritems():
				if bot.player_id != self.player_id:
					if rg.dist(loc, self.location) <= 1:
						return ['attack', loc]

			# Try to reach nearest interesting spawn point
			distances_dict = {}
			print("Self location: " + str(own_location))
			for point in self.SPAWN_SPOTS_OF_INTEREST:
				distance = rg.wdist(own_location, point)
				distances_dict.update({distance: point})

			# Get the nearest interesting location
			distances_dict_keys = distances_dict.keys()
			distances_dict_keys.sort()
			nearest_location = rg.CENTER_POINT
			for key in distances_dict_keys:
				nearest_location = distances_dict[key]
				# Check whether the point is free and isn't taken by another robot
				if nearest_location in game.robots:
					# point is taken by a robot
					continue
				loc_type = rg.loc_types(nearest_location)
				print("Types: " + str(loc_type))
				if 'normal' in loc_type and 'obstacle' not in loc_type:
					# we have found 'clear' spot
					break

			# Get next point on the way
			next_move = rg.toward(own_location, nearest_location)

			# Make sure that point is free
			loc_type = rg.loc_types(next_move)
			if 'normal' in loc_type and 'obstacle' not in loc_type and next_move not in game.robots:
				# Let's move
				print("Moving to: " + str(next_move))
				return ['move', next_move]
			else:
				# Find another way
				available_locs = rg.locs_around(own_location, filter_out=(['invalid', 'obstacle']))
				for loc in available_locs:
					if loc not in game.robots:
						return ['move', available_locs[0]]
				# Robot is blocked - no ways to move
				return ['guard']



		# stub
		return ['guard']

		"""
		# if there are enemies around, attack them
		for loc, bot in game.robots.iteritems():
			if bot.player_id != self.player_id:
				if rg.dist(loc, self.location) <= 1:
					return ['attack', loc]

		# if we're in the center, stay put
		if self.location == rg.CENTER_POINT:
			return ['guard']

		# move toward the center
		return ['move', rg.toward(self.location, rg.CENTER_POINT)]
		"""