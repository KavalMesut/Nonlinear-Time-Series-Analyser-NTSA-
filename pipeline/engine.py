"""
Pipeline execution engine with dependency resolution and caching
"""
from typing import Dict, Any, List, Optional, Set
from .node import Node
import copy


class PipelineEngine:
    """
    Manages pipeline execution with dependency checking and caching
    """
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.state: Dict[str, Any] = {}
        self.cache: Dict[str, Any] = {}
        self.params: Dict[str, Dict[str, Any]] = {}
    
    def register_node(self, node: Node, params: Optional[Dict[str, Any]] = None):
        """
        Register a node in the pipeline
        
        Args:
            node: Node to register
            params: default parameters for this node
        """
        self.nodes[node.name] = node
        if params is not None:
            self.params[node.name] = params
        else:
            self.params[node.name] = {}
    
    def set_state(self, key: str, value: Any):
        """Set a value in the state"""
        self.state[key] = value
        # Invalidate cache for nodes that depend on this
        self._invalidate_cache(key)
    
    def get_state(self, key: str) -> Any:
        """Get a value from the state"""
        return self.state.get(key)
    
    def set_params(self, node_name: str, params: Dict[str, Any]):
        """Set parameters for a node"""
        if node_name in self.nodes:
            self.params[node_name] = params
            # Invalidate cache for this node
            if node_name in self.cache:
                del self.cache[node_name]
    
    def _invalidate_cache(self, state_key: str):
        """Invalidate cache for nodes that depend on a state key"""
        to_invalidate = []
        for node_name, node in self.nodes.items():
            if state_key in node.requires:
                to_invalidate.append(node_name)
        
        for node_name in to_invalidate:
            if node_name in self.cache:
                del self.cache[node_name]
            # Recursively invalidate dependent nodes
            node = self.nodes[node_name]
            for produced in node.produces:
                self._invalidate_cache(produced)
    
    def _topological_sort(self, target_nodes: List[str]) -> List[str]:
        """
        Topological sort of nodes to determine execution order
        
        Args:
            target_nodes: list of node names to execute
        
        Returns:
            ordered list of node names
        """
        # Build dependency graph
        in_degree = {}
        graph = {}
        all_nodes = set()
        
        # Find all required nodes (including transitive dependencies)
        def add_dependencies(node_name: str):
            if node_name in all_nodes:
                return
            all_nodes.add(node_name)
            
            if node_name not in self.nodes:
                return
            
            node = self.nodes[node_name]
            for req in node.requires:
                # Find which node produces this requirement
                for other_name, other_node in self.nodes.items():
                    if req in other_node.produces:
                        add_dependencies(other_name)
        
        for target in target_nodes:
            add_dependencies(target)
        
        # Initialize graph
        for node_name in all_nodes:
            if node_name not in self.nodes:
                continue
            graph[node_name] = []
            in_degree[node_name] = 0
        
        # Build edges
        for node_name in all_nodes:
            if node_name not in self.nodes:
                continue
            node = self.nodes[node_name]
            for req in node.requires:
                # Find producer
                for other_name, other_node in self.nodes.items():
                    if req in other_node.produces:
                        graph[other_name].append(node_name)
                        in_degree[node_name] += 1
        
        # Kahn's algorithm
        queue = [n for n in in_degree if in_degree[n] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(in_degree):
            raise ValueError("Circular dependency detected in pipeline")
        
        return result
    
    def run(self, target: str, force: bool = False) -> Any:
        """
        Execute pipeline to produce target node output
        
        Args:
            target: name of target node to execute
            force: if True, ignore cache and recompute
        
        Returns:
            result from target node
        """
        if target not in self.nodes:
            raise ValueError(f"Node '{target}' not found")
        
        # Check cache
        if not force and target in self.cache:
            # Verify all requirements are still in state
            node = self.nodes[target]
            if node.can_run(self.state):
                return self.cache[target]
        
        # Determine execution order
        order = self._topological_sort([target])
        
        # Execute nodes in order
        for node_name in order:
            # Skip if already computed and in cache
            if not force and node_name in self.cache:
                node = self.nodes[node_name]
                if node.can_run(self.state):
                    continue
            
            # Run node
            node = self.nodes[node_name]
            if not node.can_run(self.state):
                missing = [r for r in node.requires if r not in self.state]
                raise RuntimeError(f"Cannot run node '{node_name}': missing {missing}")
            
            result = node.run(self.state, self.params[node_name])
            
            # Update state
            for key in node.produces:
                if key in result:
                    self.state[key] = result[key]
            
            # Cache result
            self.cache[node_name] = result
        
        return self.cache[target]
    
    def run_multiple(self, targets: List[str], force: bool = False) -> Dict[str, Any]:
        """
        Execute multiple target nodes
        
        Args:
            targets: list of target node names
            force: if True, ignore cache and recompute
        
        Returns:
            dictionary mapping target names to their results
        """
        results = {}
        for target in targets:
            results[target] = self.run(target, force=force)
        return results
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
    
    def reset(self):
        """Reset state and cache"""
        self.state.clear()
        self.cache.clear()
