"""Core designer test."""
from designers.base_designer import BaseDesigner
def test_records():
 d=BaseDesigner("x");d.record_decision("d",1,"r");d.record_assumption("a",1,"r");assert len(d.decisions)==1 and len(d.assumptions)==1
