"""Explicit alert and review state machines."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REVIEW_POLICY=json.loads((ROOT/'config'/'officer_review_policy_v1.json').read_text(encoding='utf-8'))
REVIEW_POLICY_VERSION=REVIEW_POLICY['policy_version']

ALERT_TRANSITIONS={
    'NEW':{'ACKNOWLEDGED','IN_REVIEW','PERSISTENT','ESCALATED','RESOLVED','DISMISSED'},
    'ACKNOWLEDGED':{'IN_REVIEW','MONITORING','PERSISTENT','ESCALATED','RESOLVED','DISMISSED'},
    'IN_REVIEW':{'MONITORING','ESCALATED','RESOLVED','DISMISSED'},
    'MONITORING':{'IN_REVIEW','PERSISTENT','ESCALATED','RESOLVED','DISMISSED'},
    'PERSISTENT':{'IN_REVIEW','MONITORING','ESCALATED','RESOLVED','DISMISSED'},
    'ESCALATED':{'IN_REVIEW','MONITORING','RESOLVED','DISMISSED'},
    'RESOLVED':{'REOPENED'},
    'DISMISSED':{'REOPENED'},
    'REOPENED':{'ACKNOWLEDGED','IN_REVIEW','MONITORING','PERSISTENT','ESCALATED','RESOLVED','DISMISSED'},
}

class InvalidTransition(ValueError):pass

def transition_alert(old:str,new:str)->str:
    if new not in ALERT_TRANSITIONS.get(old,set()):raise InvalidTransition(f'invalid alert transition: {old} -> {new}')
    return new

def transition_review(old:str,new:str)->str:
    if new not in REVIEW_POLICY['transitions'].get(old,[]):raise InvalidTransition(f'invalid review transition: {old} -> {new}')
    return new
