"""
Pipeline node structure for dependency management
"""
from typing import List, Dict, Any, Callable, Optional


class Node:
    """
    Pipeline node with dependency tracking
    """
    
    def __init__(self, 
                 name: str,
                 requires: List[str],
                 produces: List[str],
                 run_func: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize a pipeline node
        
        Args:
            name: unique node identifier
            requires: list of required state keys
            produces: list of state keys this node produces
            run_func: function(state, params) -> results_dict
        """
        self.name = name
        self.requires = requires
        self.produces = produces
        self.run_func = run_func
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        """Check if all required inputs are available"""
        return all(req in state for req in self.requires)
    
    def run(self, state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute node function
        
        Args:
            state: current state dictionary
            params: parameters for this node
        
        Returns:
            dictionary of produced results
        """
        if not self.can_run(state):
            missing = [req for req in self.requires if req not in state]
            raise ValueError(f"Node '{self.name}' missing requirements: {missing}")
        
        return self.run_func(state, params)
    
    def __repr__(self) -> str:
        return f"Node('{self.name}', requires={self.requires}, produces={self.produces})"
