package kdtree

import (
	"math"
)

// Point represents a point in 2D space with an ID and associated data
type Point struct {
	ID       string
	X, Y     float64
	Data     interface{}
}

// Node represents a node in the KD-Tree
type Node struct {
	Point    Point
	Left     *Node
	Right    *Node
	Depth    int
}

// KDTree represents the KD-Tree data structure
type KDTree struct {
	Root *Node
}

// NewKDTree creates a new KD-Tree from a slice of points
func NewKDTree(points []Point) *KDTree {
	if len(points) == 0 {
		return &KDTree{}
	}
	
	root := buildNode(points, 0)
	return &KDTree{Root: root}
}

// buildNode recursively builds the KD-Tree
func buildNode(points []Point, depth int) *Node {
	if len(points) == 0 {
		return nil
	}
	
	// Alternate between X and Y axis based on depth
	axis := depth % 2
	
	// Create a copy of points to sort
	pointsCopy := make([]Point, len(points))
	copy(pointsCopy, points)
	
	// Sort points by the current axis
	if axis == 0 {
		// Sort by X coordinate
		quickSortByX(pointsCopy, 0, len(pointsCopy)-1)
	} else {
		// Sort by Y coordinate
		quickSortByY(pointsCopy, 0, len(pointsCopy)-1)
	}
	
	// Select median as root
	median := len(pointsCopy) / 2
	
	node := &Node{
		Point: pointsCopy[median],
		Depth: depth,
	}
	
	// Recursively build subtrees
	node.Left = buildNode(pointsCopy[:median], depth+1)
	node.Right = buildNode(pointsCopy[median+1:], depth+1)
	
	return node
}

// QueryRadius finds all points within a given radius of the center point
func (t *KDTree) QueryRadius(center Point, radius float64) []Point {
	var result []Point
	if t.Root != nil {
		queryNode(t.Root, center, radius, &result)
	}
	return result
}

// queryNode recursively searches for points within radius
func queryNode(node *Node, center Point, radius float64, result *[]Point) {
	if node == nil {
		return
	}
	
	// Calculate distance between current node and center
	dist := distance(center, node.Point)
	
	if dist <= radius {
		*result = append(*result, node.Point)
	}
	
	// Determine which axis to compare
	axis := node.Depth % 2
	
	// Decide which subtrees to search
	var leftSearch, rightSearch bool
	
	if axis == 0 { // X-axis
		leftSearch = center.X-radius <= node.Point.X
		rightSearch = center.X+radius >= node.Point.X
	} else { // Y-axis
		leftSearch = center.Y-radius <= node.Point.Y
		rightSearch = center.Y+radius >= node.Point.Y
	}
	
	if leftSearch {
		queryNode(node.Left, center, radius, result)
	}
	if rightSearch {
		queryNode(node.Right, center, radius, result)
	}
}

// distance calculates the Euclidean distance between two points
func distance(p1, p2 Point) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// quickSortByX sorts points by X coordinate
func quickSortByX(points []Point, low, high int) {
	if low < high {
		pi := partitionByX(points, low, high)
		quickSortByX(points, low, pi-1)
		quickSortByX(points, pi+1, high)
	}
}

// quickSortByY sorts points by Y coordinate
func quickSortByY(points []Point, low, high int) {
	if low < high {
		pi := partitionByY(points, low, high)
		quickSortByY(points, low, pi-1)
		quickSortByY(points, pi+1, high)
	}
}

// partitionByX partitions the points by X coordinate
func partitionByX(points []Point, low, high int) int {
	pivot := points[high].X
	i := low - 1
	
	for j := low; j < high; j++ {
		if points[j].X <= pivot {
			i++
			points[i], points[j] = points[j], points[i]
		}
	}
	
	points[i+1], points[high] = points[high], points[i+1]
	return i + 1
}

// partitionByY partitions the points by Y coordinate
func partitionByY(points []Point, low, high int) int {
	pivot := points[high].Y
	i := low - 1
	
	for j := low; j < high; j++ {
		if points[j].Y <= pivot {
			i++
			points[i], points[j] = points[j], points[i]
		}
	}
	
	points[i+1], points[high] = points[high], points[i+1]
	return i + 1
}