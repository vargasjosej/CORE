package pru

import (
	"time"
)

// PRUType represents the 7 primitive universal relation types
type PRUType string

const (
	Entity        PRUType = "ENTITY"         // ℰ
	Sequentiality PRUType = "SEQUENTIALITY"  // 𝒮
	Modulation    PRUType = "MODULATION"     // ℳ
	Topology      PRUType = "TOPOLOGY"       // 𝒯
	Disjunction   PRUType = "DISJUNCTION"    // 𝒟
	Perspective   PRUType = "PERSPECTIVE"    // 𝔓
	Validity      PRUType = "VALIDITY"       // 𝔗
)

// TokenID uniquely identifies a token
type TokenID string

// ObserverID identifies the observer that detected the relation
type ObserverID string

// ValidityDomain represents the multidimensional domain where knowledge is valid
type ValidityDomain struct {
	FirmwarePatterns  []string               `json:"firmware_patterns"`
	CycleRange        *[2]int                `json:"cycle_range"`
	TempRangeC        *[2]float32            `json:"temp_range_c"`
	NormVersions      []string               `json:"norm_versions"`
	CustomConstraints map[string]interface{} `json:"custom_constraints"`
}

// PRURelation represents a primitive universal relation
type PRURelation struct {
	ID             string         `json:"id"`
	RelationType   PRUType        `json:"relation_type"`
	SourceID       TokenID        `json:"source_id"`
	TargetID       TokenID        `json:"target_id"`
	Strength       float32        `json:"strength"`
	Properties     map[string]interface{} `json:"properties"`
	ValidityDomain ValidityDomain `json:"validity_domain"`
	ObserverID     ObserverID     `json:"observer_id"`
	CreatedAt      time.Time      `json:"created_at"`
	UpdatedAt      time.Time      `json:"updated_at"`
}

// Token interface for all token types
type Token interface {
	GetID() TokenID
	GetObserverID() ObserverID
	GetTimestamp() time.Time
	GetBoundarySignature() map[string]interface{}
	GetContext() map[string]interface{}
}