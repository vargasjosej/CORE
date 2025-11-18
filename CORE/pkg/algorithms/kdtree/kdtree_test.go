package kdtree

import (
	"testing"
)

func TestKDTree_BasicConstruction(t *testing.T) {
	points := []Point{
		{ID: "p1", X: 2, Y: 3},
		{ID: "p2", X: 5, Y: 4},
		{ID: "p3", X: 9, Y: 6},
		{ID: "p4", X: 4, Y: 7},
		{ID: "p5", X: 8, Y: 1},
		{ID: "p6", X: 7, Y: 2},
	}
	
	tree := NewKDTree(points)
	
	if tree.Root == nil {
		t.Error("Expected root to be set, got nil")
	}
}

func TestKDTree_QueryRadius(t *testing.T) {
	points := []Point{
		{ID: "p1", X: 2, Y: 3},
		{ID: "p2", X: 5, Y: 4},
		{ID: "p3", X: 9, Y: 6},
		{ID: "p4", X: 4, Y: 7},
		{ID: "p5", X: 8, Y: 1},
		{ID: "p6", X: 7, Y: 2},
	}
	
	tree := NewKDTree(points)
	center := Point{ID: "center", X: 5, Y: 5}
	
	results := tree.QueryRadius(center, 3.0)
	
	// We expect points within radius 3 of center (5, 5)
	// Distances: p1=(2,3) -> ~2.83, p2=(5,4) -> 1, p3=(9,6) -> ~4.12, p4=(4,7) -> ~2.24, p5=(8,1) -> ~5, p6=(7,2) -> ~4.24
	// So p1, p2, p4 should be within radius 3
	if len(results) == 0 {
		t.Error("Expected some points within radius, got none")
	}
	
	// Verify that at least p2 (distance 1) is found
	foundP2 := false
	for _, p := range results {
		if p.ID == "p2" {
			foundP2 = true
			break
		}
	}
	
	if !foundP2 {
		t.Error("Expected to find point p2 within radius")
	}
}

func TestKDTree_EmptyTree(t *testing.T) {
	tree := NewKDTree([]Point{})
	
	center := Point{ID: "center", X: 0, Y: 0}
	results := tree.QueryRadius(center, 1.0)
	
	if len(results) != 0 {
		t.Errorf("Expected 0 results from empty tree, got %d", len(results))
	}
}

func TestKDTree_SinglePoint(t *testing.T) {
	points := []Point{
		{ID: "p1", X: 5, Y: 5},
	}
	
	tree := NewKDTree(points)
	center := Point{ID: "center", X: 5, Y: 5}
	
	results := tree.QueryRadius(center, 1.0)
	
	if len(results) != 1 {
		t.Errorf("Expected 1 result from single point tree, got %d", len(results))
	}
	
	if results[0].ID != "p1" {
		t.Errorf("Expected point ID 'p1', got '%s'", results[0].ID)
	}
}