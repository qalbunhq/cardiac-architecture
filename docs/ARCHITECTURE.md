# Cardiac Architecture

## Mechanism 1: Autonomous Sensing Layer
A continuous coherence score (0.0-1.0) summarizes system state from runtime telemetry. High coherence enables autonomous routing. Low coherence forces escalation.

## Mechanism 2: Somatic Marker Library
Every completed task writes a marker with task signature, chosen agent, outcome, confidence, surprise, effort, downstream impact, and composite valence.

## Mechanism 3: Pre-Cognitive Routing
Before LLM reasoning, the router queries nearest markers, estimates predicted valence/confidence, then routes autonomously or escalates.

## Core Flow
Task -> Coherence compute -> Marker query -> Route decision -> Execute -> Marker write.
