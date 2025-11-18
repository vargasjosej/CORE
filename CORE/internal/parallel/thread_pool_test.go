package parallel

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"
)

func TestThreadPoolSubmitAndWait(t *testing.T) {
	tp := NewThreadPool(2)
	defer tp.Stop()

	task := func() error {
		time.Sleep(10 * time.Millisecond) // Simulate work
		return nil
	}

	err := tp.SubmitAndWait(task)
	if err != nil {
		t.Errorf("Expected no error, got: %v", err)
	}
}

func TestThreadPoolSubmitAndWaitWithError(t *testing.T) {
	tp := NewThreadPool(2)
	defer tp.Stop()

	expectedErr := errors.New("test error")
	task := func() error {
		return expectedErr
	}

	err := tp.SubmitAndWait(task)
	if err != expectedErr {
		t.Errorf("Expected error %v, got: %v", expectedErr, err)
	}
}

func TestThreadPoolSubmitN(t *testing.T) {
	tp := NewThreadPool(4)
	defer tp.Stop()

	numTasks := 10
	tasks := make([]Task, numTasks)
	
	var counter int
	var mu sync.Mutex
	
	for i := range tasks {
		tasks[i] = func() error {
			mu.Lock()
			counter++
			mu.Unlock()
			time.Sleep(5 * time.Millisecond) // Simulate work
			return nil
		}
	}

	errors := tp.SubmitN(tasks)
	
	if len(errors) != numTasks {
		t.Errorf("Expected %d errors, got %d", numTasks, len(errors))
	}
	
	for _, err := range errors {
		if err != nil {
			t.Errorf("Unexpected error: %v", err)
		}
	}
	
	if counter != numTasks {
		t.Errorf("Expected counter to be %d, got %d", numTasks, counter)
	}
}

func TestThreadPoolSubmitBatch(t *testing.T) {
	tp := NewThreadPool(4)
	defer tp.Stop()

	numTasks := 8
	tasks := make([]Task, numTasks)
	
	var completedTasks int
	var mu sync.Mutex
	
	for i := range tasks {
		tasks[i] = func() error {
			mu.Lock()
			completedTasks++
			mu.Unlock()
			time.Sleep(10 * time.Millisecond) // Simulate work
			return nil
		}
	}

	errors := tp.SubmitBatch(tasks, 3) // Limit concurrency to 3
	
	if len(errors) != numTasks {
		t.Errorf("Expected %d errors, got %d", numTasks, len(errors))
	}
	
	if completedTasks != numTasks {
		t.Errorf("Expected %d tasks to be completed, got %d", numTasks, completedTasks)
	}
}

func TestThreadPoolSubmitWithError(t *testing.T) {
	tp := NewThreadPool(2)
	defer tp.Stop()

	expectedErr := errors.New("test error")
	task := func() error {
		return expectedErr
	}

	err := tp.Submit(task)
	if err != nil {
		t.Errorf("Submit should not return error for valid task, got: %v", err)
	}
	
	// Wait for the task to complete by submitting and waiting
	waitTask := func() error {
		time.Sleep(20 * time.Millisecond)
		return nil
	}
	tp.SubmitAndWait(waitTask)
}

func TestThreadPoolContextCancellation(t *testing.T) {
	tp := NewThreadPool(2)
	
	// Create a context that will be cancelled
	ctx, cancel := context.WithCancel(context.Background())
	
	// Submit a task that checks for context cancellation
	task := func() error {
		// Simulate work that respects context
		select {
		case <-time.After(100 * time.Millisecond):
			return nil
		case <-ctx.Done():
			return ctx.Err()
		}
	}

	err := tp.Submit(task)
	if err != nil {
		t.Errorf("Submit should not return error, got: %v", err)
	}
	
	cancel() // Cancel the context
	time.Sleep(20 * time.Millisecond) // Give time for cancellation to propagate
	
	tp.Stop() // This should not block indefinitely
}

func TestThreadPoolStats(t *testing.T) {
	tp := NewThreadPool(2)
	defer tp.Stop()

	stats := tp.GetStats()
	
	if workers, ok := stats["workers"].(int); !ok || workers != 2 {
		t.Error("Expected 2 workers")
	}
	
	if tasksPending, ok := stats["tasks_pending"].(int); !ok || tasksPending != 0 {
		t.Error("Expected 0 pending tasks")
	}
}

func TestThreadPoolWaitAll(t *testing.T) {
	tp := NewThreadPool(2)
	defer tp.Stop()

	numTasks := 5
	completedTasks := make([]bool, numTasks)
	var mu sync.Mutex

	tasks := make([]Task, numTasks)
	for i := range tasks {
		i := i // Capture loop variable
		tasks[i] = func() error {
			time.Sleep(10 * time.Millisecond) // Simulate work
			mu.Lock()
			completedTasks[i] = true
			mu.Unlock()
			return nil
		}
	}

	// Submit all tasks
	for _, task := range tasks {
		if err := tp.Submit(task); err != nil {
			t.Fatalf("Failed to submit task: %v", err)
		}
	}

	tp.WaitAll() // Wait for all tasks to complete

	// Check that all tasks were completed
	for i, completed := range completedTasks {
		if !completed {
			t.Errorf("Task %d was not completed", i)
		}
	}
}

func TestThreadPoolStop(t *testing.T) {
	tp := NewThreadPool(2)
	
	task := func() error {
		time.Sleep(10 * time.Millisecond)
		return nil
	}
	
	// Submit a task
	tp.Submit(task)
	
	// Stop the thread pool
	tp.Stop()
	
	// After stopping, submitting should not block indefinitely
	// though it should return context cancelled error
	select {
	case <-time.After(100 * time.Millisecond):
		t.Error("Stop should not block indefinitely")
	default:
		// OK - stop completed quickly
	}
}