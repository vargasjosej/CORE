package pru

import (
	"time"
)

// SignalToken represents a signal observation token
type SignalToken struct {
	ID                TokenID                    `json:"id"`
	ObserverID        ObserverID                 `json:"observer_id"`
	TimestampNs       int64                      `json:"timestamp_ns"`
	BoundarySignature map[string]interface{}     `json:"boundary_signature"`
	Context           map[string]interface{}     `json:"context"`
	Value             float32                    `json:"value"`
	SignalType        string                     `json:"signal_type"` // digital|analog|counter
	EdgeCount         int                        `json:"edge_count"`
	FrequencyHz       *float32                   `json:"frequency_hz"`
}

func (st *SignalToken) GetID() TokenID {
	return st.ID
}

func (st *SignalToken) GetObserverID() ObserverID {
	return st.ObserverID
}

func (st *SignalToken) GetTimestamp() time.Time {
	return time.Unix(0, st.TimestampNs)
}

func (st *SignalToken) GetBoundarySignature() map[string]interface{} {
	return st.BoundarySignature
}

func (st *SignalToken) GetContext() map[string]interface{} {
	return st.Context
}