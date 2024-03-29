#! /usr/bin/python

'''
	matcher.py

	Author : Soumya Mandi
	matcher.py we will follow this order .
	this script is to be called using
	$./matcher.py list1.txt list2.txt

	list2.txt will be from smaller image
'''

'''
	#PARAMETERS to be changed
		MAXIMUM_PAIRWISE_DISTANCE
		THRESHOLD_DIST
		THRESHOLD_BETA1
		THRESHOLD_BETA2

'''
import networkx as nx,sys
import math
import copy
import logging

MAXIMUM_PAIRWISE_DISTANCE = 100
MAXIMUM_EUCLIDEAN_DISTANCE = -1 #the maximum distance that can be possible useful for normalization purpose
ISO_FACTOR = 1.40625
ANSI_FACTOR = 2.000

logging.basicConfig( filename='info.log',filemode='w',level=logging.DEBUG,format='%(message)s' )

def conv_to_numbers( minutiaes ) :
	numbers = []
	for m in minutiaes :
		numbers.append( [  int( mi ) for mi in m ] )
		
	return numbers

def sort_2d( minutiaes ) :
	'''
		First sorts minutiaes by y and then by x and then returns it.
	'''
	#minutiaes.sort( key=lambda x: x[1] )
	#arrange the minutiaes so as to sort them lexicographically as they are represented in x,y format. change to y,x
	y_x_format_minutiaes = [ [ item[1],item[0],item[2] ] for item in minutiaes ]
	sorted_minutiaes = sorted( y_x_format_minutiaes  )
	x_y_format_minutiaes = [ [ item[1],item[0],item[2] ] for item in sorted_minutiaes ]

	return x_y_format_minutiaes

def calculate_angle( minutiaes1,minutiaes2 ) :
	'''
	This returns an angle between 0 and 180
	'''

	#logging.info(  str(minutiaes1)+ str( minutiaes2  ) )

	angle = - math.degrees( math.atan( ( minutiaes1[1]-minutiaes2[1] )/( minutiaes1[0]-minutiaes2[0]+0.000000001 ) ) )

	if angle < 0 :
		#logging.info( 180+angle )
		return 180+angle
	#logging.info( angle )
	return angle

def euclidean_distance( p1,p2 ) :
	return math.sqrt( (p2[0]-p1[0])**2 + ( p2[1]-p1[1] )**2 )


#iptable is in the form of [ distance,beta1,beta2,i,j ]

def build_intra_table( minutiaes ) :
	iptable = []
	distances = [] #list where each entry is a pairwise distance
	for i in range( len(minutiaes )-1 ) :
		k = i+1
		for j in range( k,len(minutiaes) ) :
			##print minutiaes[i],minutiaes[k]
			##print '(i,j) : ( %d,%d )'%(i,j)
			distance = euclidean_distance( minutiaes[i][ 0:2 ],minutiaes[j][ 0:2 ] )
			#print 'dist is : ',distance
			distances.append( distance )
			if distance > MAXIMUM_PAIRWISE_DISTANCE : #if distance greater than a threshold then put the entry into the table
				continue
			angle_of_line = calculate_angle( minutiaes[i][ 0:2 ],minutiaes[j][ 0:2 ] )

			
			#the factor*angle follows because of the way ansi or iso stores the minutiaes
			beta1 = ANSI_FACTOR*minutiaes[i][2] - angle_of_line
			beta2 = ANSI_FACTOR*minutiaes[j][2] - angle_of_line

			if beta1 < beta2 :
				iptable.append( ( distance, beta1,beta2,i,j ) )
			else :
				iptable.append( ( distance, beta2,beta1,j,i ) )

	distances.sort()
	'''
	#print 'the distances in sorted order are : '
	for entry in distances :
		#print entry
	'''
	return iptable



def use_entry( index_list,li ) : #return first Not-None value
	""" Returns the first value that is not None """
	for i in index_list :
		if li[i] :
			return i


def get_tokens( ) :
	limit = 50

	count = 1
	while True :
		yield 'm'+str( count )

		if count > 50 :
			break
		count += 1

def build_spanning_tree( ct ) :
	'''Build a spanning tree using the edge information in the spanning tree
		ct is compatibility table
	'''
	#print '\n\n\n#build_spanning_tree'
	G1 = nx.Graph() #graph for the first minutiae set
	G2 = nx.Graph() #graph for the first minutiae set

	tokens = get_tokens()

	dict1={}
	dict2={}

	for entry in ct :
		#rename such that entry[0] and entry[2] gets the same label
		#print 'entry is : ', entry
		if dict1.get( entry[0] ) :
			#do nothing
			pass
		else :
			dict1[ entry[0] ] = dict2[ entry[2] ] = next( tokens )
		
		if dict1.get( entry[1] ) :
			#do nothing
			pass
		else :
			dict1[ entry[1] ] = dict2[ entry[3] ]  = next( tokens )

		G1.add_edge( dict1[ entry[0] ],dict1[ entry[1] ],weight=entry[4] )
		G2.add_edge( dict2[ entry[2] ],dict2[ entry[3] ],weight=entry[4] )

	#print 'G1.edges are : ', G1.edges()
	#print 'G2.edges are : ', G2.edges()


	min_span_g1 = nx.minimum_spanning_tree( G1 )
	min_span_g2 = nx.minimum_spanning_tree( G2 )

	return dict1,dict2,min_span_g1,min_span_g2



def remove_value_from_index( removable,i1,i2 ) :
	''' find key which has removable as value
	and remove them
	'''
	##print '#remove_value_from_index '
	##print 'i1 is : ',i1
	##print 'i2 is : ',i2

	##print 'removable is : ',removable
	for key in i1 :
		if removable in i1[ key ] :
			i1[ key ].remove( removable )
	
	for key in i2 :
		if removable in i2[ key ] :
			i2[ key ].remove( removable )



def get_disjoint_trees_dynamic( tree_list ) :
	'''Now get all the disjoint trees using dynamic programming
	e.g [ [a,b,c],[a,b],[c,d] ] ==> [a,b,c,d] not [ a,b,c ]
	'''
	num_trees = len( tree_list )

	size_list = [] #maximum size that has all the disjoint trees. This list is a list which stores that maximum size for each index
	size_list.append( len( tree_list[0].nodes() ) )

	nodes_list = [] #stores all the nodes that would be present at that index so as to have maximum number of nodes 
	nodes_list.append( tree_list[0].nodes() )

	included_trees = [] #stores index of the trees which are used for thee tree set stored at the index giving maximum size
	included_trees.append( [0] )

	for i in range( 1,num_trees ) :
		max_index = None #has the index which is disjoint from the current tree
		maximum = 0 #has the number of nodes in each index

		#print '#dynamic i is : ',i

		for j in range( 0,i ) :
			#print 'and operation for ( %d,%d ) ' % ( i,j )
			#print 'nodes_list[j] is :',nodes_list[ j ]
			#print 'tree_list[i].nodes() is :',tree_list[ i ].nodes()
			if not ( set( nodes_list[ j ] ) & ( set( tree_list[ i ].nodes() ) ) ) : #The part for dynamic programming
				#print 'Entered'
				if maximum < size_list[ j ] :
					maximum =  size_list[ j ]
					#print 'maximum is : ',maximum
					max_index = j

		##print 'tree_list[ %d ] is : %s',%( i,'hi' )
		if max_index is not None :
			#print 'tree_list[ i ] is :', tree_list[i].nodes()
			#print 'tree_list[ max_index ] is :', ( tree_list[ max_index ].nodes(), max_index )
			#print 'max_index : size[ %d ] is : ',size_list[ max_index ]
			size_list.append( len( tree_list[ i ].nodes() ) + size_list[ max_index ]  ) 
			#print 'size_list is : ',size_list
			nodes_list.append( nodes_list[ max_index ] + tree_list[ i ].nodes() )
			included_trees.append(  included_trees[ max_index ] + [ i ]  )
		else :
			size_list.append( len( tree_list[ i ].nodes() ) )
			#print 'size_list NA is : ',size_list
			#print 'nodes_list is : ',nodes_list
			#print 'current_nodes are : ',tree_list[ i ].nodes()
			nodes_list.append( tree_list[ i ].nodes() )
			included_trees.append( [ i ] )

	return size_list,included_trees



def get_disjoint_trees( tree_list ) :
	'''Now  get all the disjoint trees 
	@param
	tree_list is a list of trees( networkx graphs ) in order of size . decreasing here
	'''

	disjoint_trees = [] # a list of trees. each tree is disjoint in term of nodes
	included_nodes = []
	for tree in tree_list :
		if set( tree.nodes() ) & set( included_nodes ) :	
			pass
		else :
			included_nodes += tree.nodes()
			disjoint_trees.append( tree )

	return disjoint_trees



def build_ct_and_indexes( iptable1,iptable2 ) :
	'''
		builds compatibility_table and indexes and returns them.
	'''

	compatibility_table = []
	
	mapping1 = {}
	mapping2 = {}
	THRESHOLD_DIST = 8.0
	THRESHOLD_BETA1 = 20.0
	THRESHOLD_BETA2 = 20.0
	for i in range( len( iptable1 ) ) :
		for j in range( len( iptable2 ) ) :
			point_dist = abs( iptable1[ i ][ 0 ]-iptable2[j][0] )
			beta1_dist = abs( iptable1[i][1] - iptable2[j][1] )
			beta2_dist = abs( iptable1[i][2] - iptable2[j][2] )
			#TODO : Find the shortest distance
			if point_dist <= THRESHOLD_DIST and  beta1_dist <= THRESHOLD_BETA1 and beta2_dist  <= THRESHOLD_BETA2 :
				compatibility_table.append( ( iptable1[i][3],iptable1[i][4],iptable2[j][3],iptable2[j][4],iptable1[i][0] ) )
				logging.info( ( iptable1[i][3],iptable1[i][4],iptable2[j][3],iptable2[j][4] ) )
				#print 'compatibility_table is : ',compatibility_table

				#keep track how many elements are mapped from one to another

				#From 1 to 2 mapping
				if mapping1.get( iptable1[i][3] ) :
					if mapping1[ iptable1[i][3] ].get( iptable2[j][3] ) :
						mapping1[ iptable1[i][3] ][ iptable2[j][3] ] += 1
					else :
						mapping1[ iptable1[i][3] ][ iptable2[j][3] ] = 1
				else :
					mapping1[ iptable1[i][3] ] = { iptable2[j][3] : 1 }


				if mapping1.get( iptable1[i][4] ) :
					if mapping1[ iptable1[i][4] ].get( iptable2[j][4] ) :
						mapping1[ iptable1[i][4] ][ iptable2[j][4] ] += 1
					else :
						mapping1[ iptable1[i][4] ][ iptable2[j][4] ] = 1
				else :
					mapping1[ iptable1[i][4] ] = { iptable2[j][4] : 1 }


				#From 2 to 1 mapping

				if mapping2.get( iptable2[j][3] ) :
					if mapping2[ iptable2[j][3] ].get( iptable1[i][3] ) :
						mapping2[ iptable2[j][3] ][ iptable1[i][3] ] += 1
					else :
						mapping2[ iptable2[j][3] ][ iptable1[i][3] ] = 1
				else :
					mapping2[ iptable2[j][3] ] = { iptable1[i][3] : 1 }

				if mapping2.get( iptable2[j][4] ) :
					if mapping2[ iptable2[j][4] ].get( iptable1[i][4] ) :
						mapping2[ iptable2[j][4] ][ iptable1[i][4] ] += 1
					else :
						mapping2[ iptable2[j][4] ][ iptable1[i][4] ] = 1
				else :
					mapping2[ iptable2[j][4] ] = { iptable1[i][4] : 1 }

	
	logging.info('compatibility table is : ' )
	logging.info( compatibility_table )

	return compatibility_table,mapping1,mapping2


def get_boundaries( minutiaes_in_box,minutiaes ) :
	'''
	returns ( leftmost co_ordinate, uppermost coordinate, rightmost coordinate , bottomost coordinate )
	'''
	#print 'minutiaes are : ', minutiaes
	#print 'in get_boundaries() : ',minutiaes.index( min( minutiaes, key= lambda x : x[0] ) )

	if not minutiaes_in_box :
		return None	
		#return ( minutiaes.index( min( minutiaes_in_box, key= lambda x : x[0] ) ) , minutiaes.index( min( minutiaes_in_box, key = lambda x : x[1] ) ), minutiaes.index( max( minutiaes_in_box, key = lambda x : x[0] ) ), minutiaes.index( max( minutiaes_in_box, key=lambda x : x[1] ) ) )
	return ( minutiaes.index( min( minutiaes_in_box, key= lambda x : x[0] ) ) , minutiaes.index( min( minutiaes_in_box, key = lambda x : x[1] ) ), minutiaes.index( max( minutiaes_in_box, key = lambda x : x[0] ) ), minutiaes.index( max( minutiaes_in_box, key=lambda x : x[1] ) ) )



def map_reduce( table ) :
	'''
		table is the original compatibility table. Do reduction in it to reduce conflicts :D
		Approach first make edges, add to G1 , then sort according to weight. Start removing edges
		create another tree. Then remaining edges in G, delete the entries corresponding to them. 
	'''
	index1 = {} #keeps track of the minutiaes from minutiaes1
	index2 = {} #keeps track of the minutiaes from minutiaes2

	G = nx.DiGraph()
	G_out = nx.DiGraph()
	for i,entry in enumerate(table) :
		
		#update the indexes this has to done for each entry
		if index1.get( entry[0] ) :
			index1[ entry[0] ] += [i]
		else :
			index1[ entry[0] ] = [i]

		if index1.get( entry[1] ) :
			index1[ entry[1] ] += [i]
		else :
			index1[ entry[1] ] = [i]

		if index2.get( entry[2] ) :
			index2[ entry[2] ] += [i]
		else :
			index2[ entry[2] ] = [i]

		if index2.get( entry[3] ) :
			index2[ entry[3] ] += [i]
		else :
			index2[ entry[3] ] = [i]

		if  ( entry[0],entry[2] ) in G.edges() : #update weight by 1
			G.add_edge( entry[0],entry[2],weight=G.get_edge_data( entry[0],entry[2] )['weight']+1 )
		else :
			G.add_edge( entry[0],entry[2],weight=1 )

		if  ( entry[1],entry[3] ) in G.edges() : #update weight by 1
			G.add_edge( entry[1],entry[3],weight=G.get_edge_data( entry[1],entry[3] )['weight']+1 )
		else :
			G.add_edge( entry[1],entry[3],weight=1 )

	
	#print '\n\n\n\n\n\n\n'
	#print G.edge


	#Get an iterator over the edges and add the suitable ones to G_out
	edge_data = list( G.edges_iter( data=True ) )
	edge_data.sort( key=lambda x : x[2]['weight'],reverse=True )

	#print '\n\n\n\n\n\nedge_data'
	#print edge_data

	for edge in edge_data : 
		if G_out.has_node( edge[0] ) or G_out.has_node( edge[1] ) : # if node is already present don't add the edge as it would again cause conflict
			pass
		else :
			G_out.add_edge( *edge )
			G.remove_edge( *edge[0:2] )
		
	#print '\n\n\n\n\n'
	#print G_out.edge

	#print '\n\n\n\n\n'
	#print G.edge

	#TODO
	for edge in list( G.edges_iter( data=True ) ) :
		index_in_ct = list( set( index1[ edge[0] ] ) & set( index2[ edge[1] ] ) )

		for i in index_in_ct :
			table[i] = None
			index1[ edge[0] ].remove( i )
	#print 'index1 is : ', index1
	#print 'index2 is : ', index2

	#print '\n\n\n\ntable is : ', table

	table = [ item for item in table if item ]
	#print 'table final is : ', table
	#print 'len(table) is : ', len( table )

	return table





#Find the mapping from 1 to 2. 1 is the first argument

def get_mapping( compatibility_table ) :
	#mapping from 2nd to 1st is required here. small -> large
	#print 'in get_mapping()'
	#print compatibility_table
	mapping = {}
	for entry in compatibility_table :
		#print 'entry in compatibility_table',entry
		#print 'keys are : ',( entry[2],entry[3] )
		if mapping.get( entry[2] ) :
			if mapping[ entry[2] ] != entry[0] :
				#print 'gadbad hai bhai'
				#print 'the entry is : ',( mapping[ entry[2] ],entry[0] )
				#print 'the new should be : ',( entry[2],entry[0] )
				pass
			pass
		else :
			mapping[ entry[2] ]  = entry[0]

		if mapping.get( entry[3] ) :
			if mapping[ entry[3] ] != entry[1] :
				#print 'bahut gadbad hai bhai'
				#print 'the entry is : ',( mapping[ entry[3] ],entry[1] )
				#print 'the new should be : ',( entry[3],entry[1] )
				pass
			pass
		else :
			mapping[ entry[3] ] = entry[1]
	
	return mapping
#Now make a boundary and search for the minutiaes inside from dict1
def get_convex_hull( boundaries,mapping ) :
	#the limits are 260x300 so 259x299
	#print 'Inside get_convex_hull ', boundaries

	if minutiaes1[ mapping[ boundaries[ 0 ] ] ][0] - minutiaes2[ boundaries[0] ][0] < 0 :
		left_x_of_hull = 0	
	else :
		left_x_of_hull = minutiaes1[ mapping[ boundaries[ 0 ] ] ][0] - minutiaes2[ boundaries[0] ][0]
	if minutiaes1[ mapping[ boundaries[ 1 ] ] ][1] - minutiaes2[ boundaries[1] ][1] < 0 :
		top_y_of_hull  = 0
	else :
		top_y_of_hull =  minutiaes1[ mapping[ boundaries[ 1 ] ] ][1] - minutiaes2[ boundaries[1] ][1]
		
	if minutiaes1[ mapping[ boundaries[ 0 ] ] ][0] + 259 - minutiaes2[ boundaries[0] ][0] > 259 :#assuming 260 the base size
		right_x_of_hull = 259 
	else :
		right_x_of_hull = minutiaes1[ mapping[ boundaries[ 0 ] ] ][0] + 259 - minutiaes2[ boundaries[0] ][0]

	if minutiaes1[ mapping[ boundaries[ 0 ] ] ][1] +  299 - minutiaes2[ boundaries[0] ][1] > 299 :
		bottom_y_of_hull = 299
	else :
		bottom_y_of_hull = minutiaes1[ mapping[ boundaries[ 0 ] ] ][1] +  299 - minutiaes2[ boundaries[0] ][1]
	return ( left_x_of_hull, top_y_of_hull, right_x_of_hull, bottom_y_of_hull )

	
def get_inside_the_boundary( points,minutiaes ) :
	"""
	Given a set of coordinates and minutiaes it gives the minutiaes which lies within the 
	rectangle formed by the points.
	"""

	bounded_minutiaes = []

	for entry in minutiaes :
		if entry[0] >= points[0] and entry[1] >= points[1] and entry[0] <= points[2] and entry[1] <= points[3] :
			bounded_minutiaes.append( entry )

	
	return bounded_minutiaes

def fetch_minutiaes_list( fileName1, fileName2 ) :
	"""
		Given two ANSI format minutiae files, make two list minutiaes1 and minutiaes2
		such that minutiaes1 has the minutiaes from the larger image
	"""

	minutiaes1 = []
	minutiaes2 = []

	f1,f2 = open( fileName1,'r' ),open( fileName2,'r' )
	lines1,lines2 = f1.readlines(),f2.readlines()
	dimensions1 = [ int(item) for item in lines1.pop( 0 ).split()[ 0:2 ] ] #the first line is the dimension
	dimensions2 = [ int(item) for item in lines2.pop( 0 ).split()[ 0:2 ] ]


	list1 = [ a.split()[ :3 ] for a in lines1 ]
	list2 = [ a.split()[ :3 ] for a in lines2 ]

	minutiaes_in_list1 = conv_to_numbers( list1 )
	minutiaes_in_list1 = sort_2d( minutiaes_in_list1 )

	minutiaes_in_list2 = conv_to_numbers( list2 )
	minutiaes_in_list2 = sort_2d( minutiaes_in_list2 )

	if dimensions1 > dimensions2 :
		minutiaes1,minutiaes2 = minutiaes_in_list1,minutiaes_in_list2
	else :
		minutiaes2,minutiaes1 = minutiaes_in_list1,minutiaes_in_list2

	return minutiaes1,minutiaes2
	
if __name__ == "__main__" :
	if len( sys.argv ) < 3 :
		#print 'You are doing it wrong!\nThe currect usage is : python matcher.py list1.txt list2.txt'
		exit()
	

	minutiaes1,minutiaes2 = fetch_minutiaes_list( sys.argv[1],sys.argv[2] )
	
	iptable1 = build_intra_table( minutiaes1 )
	iptable2 = build_intra_table( minutiaes2 )
	

	compatibility_table,mapping1,mapping2 = build_ct_and_indexes( iptable1,iptable2 )
	reduced_compatibility_table = map_reduce( compatibility_table ) #resolve conflicts that arises from build_ct_and_indexes
	mapping = get_mapping( reduced_compatibility_table ) #mapping is map from minutiaes in 2 to minutiaes in 1

	#print 'mapping is : ', mapping

	dict1,dict2,Spanning_forest_1,Spanning_forest_2 = build_spanning_tree( reduced_compatibility_table )
	
	
	minutiaes2_in_box = [ minutiaes2[ item ] for item in mapping.keys() ] #minutiaes2_in_box is the minutiaes that are in the smaller image that are mapped to some minutiae in larger image.
	
	
	#print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'
	#print 'minutiaes2_in_box is : ', minutiaes2_in_box
	
	#print '\n\n\n\n\n\n'
	#print 'minutiaes2 is : ', minutiaes2
	
	#print '\n\n\n\n\n\n'
	boundaries = get_boundaries( minutiaes2_in_box,minutiaes2 )
	minutiaes1_in_box = 0

	if boundaries :
		
		convex_points = get_convex_hull( boundaries,mapping )
		#print 'convex_points is : ',convex_points
	
		#print  'The boundaries are :' ,( x_left, y_top, x_right, y_bottom )
		
		#Now count the minutiaes from minutiae1 which fall under the box
		minutiaes1_in_box = get_inside_the_boundary( convex_points,minutiaes1 )
		
	else :
		pass

	#score = ( len(  mapping )**2*1.0 )/( len( minutiaes1_in_box )*len( minutiaes2 ) ) 
	
	#print 'len(mapping) is : %d ',len( mapping )
	#print 'len( minutiaes1_in_box is : %d ', len( minutiaes1_in_box )
	#print 'len( minutiaes2 ) is : %d ', len( minutiaes2 )
	
	#print 'score is : %f'%( score, )

	#print 'another score is : ',( (len( mapping )*1.0)/len( minutiaes2 ) )
	score_2 = 0
	if len( minutiaes1 ) == 0 or len( minutiaes2 ) == 0 :
		score_2 = 0
	else :
		score_2 = ( len( mapping )*1.0 )/min( len( minutiaes1 ),len( minutiaes2 ) )
	print score_2
	
	
