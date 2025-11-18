package pru

import (
	"testing"
	"time"
)

func TestVisualToken_GetID(t *testing.T) {
	token := &VisualToken{
		ID: "test-id",
	}
	
	if token.GetID() != "test-id" {
		t.Errorf("Expected ID 'test-id', got '%s'", token.GetID())
	}
}

func TestVisualToken_GetTimestamp(t *testing.T) {
	now := time.Now().UnixNano()
	token := &VisualToken{
		TimestampNs: now,
	}
	
	if !token.GetTimestamp().Equal(time.Unix(0, now)) {
		t.Errorf("Timestamp mismatch")
	}
}

func TestPRURelationCreation(t *testing.T) {
	relation := &PRURelation{
		ID:           "test-relation",
		RelationType: Entity,
		SourceID:     "source-1",
		TargetID:     "target-1",
		Strength:     0.9,
		Properties:   map[string]interface{}{"test": true},
		ObserverID:   "observer-1",
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
		ValidityDomain: ValidityDomain{
			FirmwarePatterns: []string{"test-fw-*"},
		},
	}
	
	if relation.RelationType != Entity {
		t.Errorf("Expected relation type 'Entity', got '%s'", relation.RelationType)
	}
	
	if relation.Strength != 0.9 {
		t.Errorf("Expected strength 0.9, got %f", relation.Strength)
	}
}