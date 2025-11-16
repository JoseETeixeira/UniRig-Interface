"""
Skeleton compatibility detection for motion retargeting.
Compares source (motion clip) and target (rigged model) skeletons to determine if retargeting is feasible.
"""

import logging
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class SkeletonCompatibilityChecker:
    """
    Checks compatibility between source and target skeletons for motion retargeting.
    """
    
    # Essential bones for humanoid skeletons
    HUMANOID_REQUIRED_BONES = {
        'hips', 'spine', 'chest', 'neck', 'head',
        'leftshoulder', 'leftarm', 'leftforearm', 'lefthand',
        'rightshoulder', 'rightarm', 'rightforearm', 'righthand',
        'leftupleg', 'leftleg', 'leftfoot',
        'rightupleg', 'rightleg', 'rightfoot'
    }
    
    # Essential bones for quadruped skeletons
    QUADRUPED_REQUIRED_BONES = {
        'hips', 'spine', 'chest', 'neck', 'head',
        'frontleftleg', 'frontleftfoot',
        'frontrightleg', 'frontrightfoot',
        'backleftleg', 'backleftfoot',
        'backrightleg', 'backrightfoot',
        'tail'
    }
    
    # Bone name variations/aliases for fuzzy matching
    BONE_ALIASES = {
        'hips': ['hip', 'pelvis', 'root'],
        'spine': ['spine1', 'spine01', 'spinebase'],
        'chest': ['spine2', 'spine02', 'spine3', 'upperchest', 'thorax'],
        'neck': ['neck1', 'neck01'],
        'head': ['skull'],
        'leftshoulder': ['l_shoulder', 'shoulderleft', 'left_clavicle', 'clavicleleft'],
        'leftarm': ['l_arm', 'upperarmleft', 'left_upperarm', 'leftupperarm'],
        'leftforearm': ['l_forearm', 'lowerarmleft', 'left_lowerarm', 'leftlowerarm'],
        'lefthand': ['l_hand', 'handleft', 'left_wrist', 'wristleft'],
        'rightshoulder': ['r_shoulder', 'shoulderright', 'right_clavicle', 'clavicleright'],
        'rightarm': ['r_arm', 'upperarmright', 'right_upperarm', 'rightupperarm'],
        'rightforearm': ['r_forearm', 'lowerarmright', 'right_lowerarm', 'rightlowerarm'],
        'righthand': ['r_hand', 'handright', 'right_wrist', 'wristright'],
        'leftupleg': ['l_upleg', 'thighleft', 'left_thigh', 'leftthigh', 'left_upperleg'],
        'leftleg': ['l_leg', 'shinleft', 'left_shin', 'calfLleft', 'left_lowerleg'],
        'leftfoot': ['l_foot', 'footleft', 'left_ankle', 'ankleleft'],
        'rightupleg': ['r_upleg', 'thighright', 'right_thigh', 'rightthigh', 'right_upperleg'],
        'rightleg': ['r_leg', 'shinright', 'right_shin', 'calfright', 'right_lowerleg'],
        'rightfoot': ['r_foot', 'footright', 'right_ankle', 'ankleright'],
        'tail': ['tail1', 'tail01', 'tailbase'],
        'frontleftleg': ['frontleftupperleg', 'fl_leg', 'leftfrontleg'],
        'frontrightleg': ['frontrightupperleg', 'fr_leg', 'rightfrontleg'],
        'backleftleg': ['backleftupperleg', 'bl_leg', 'lefthindleg'],
        'backrightleg': ['backrightupperleg', 'br_leg', 'righthindleg'],
    }
    
    def __init__(self, fuzzy_matching: bool = True, compatibility_threshold: float = 0.7):
        """
        Initialize skeleton compatibility checker.
        
        Args:
            fuzzy_matching: Enable fuzzy bone name matching (e.g., 'LeftArm' matches 'left_arm')
            compatibility_threshold: Minimum compatibility score (0-1) to consider skeletons compatible
        """
        self.fuzzy_matching = fuzzy_matching
        self.compatibility_threshold = compatibility_threshold
        logger.info(f"SkeletonCompatibilityChecker initialized (fuzzy={fuzzy_matching}, threshold={compatibility_threshold})")
    
    def check_compatibility(
        self,
        source_skeleton: Dict,
        target_skeleton: Dict
    ) -> Dict:
        """
        Check compatibility between source (motion) and target (rigged model) skeletons.
        
        Args:
            source_skeleton: Skeleton data from motion clip (from SkeletonExtractor or BVH parser)
            target_skeleton: Skeleton data from rigged model (from SkeletonExtractor)
        
        Returns:
            Dictionary with compatibility analysis:
            {
                "compatible": bool,
                "compatibility_score": float (0-1),
                "missing_bones": List[str],  # Bones in source but not in target
                "extra_bones": List[str],     # Bones in target but not in source
                "matched_bones": List[str],   # Bones found in both
                "skeleton_type_match": bool,  # Whether skeleton types match
                "source_type": str,
                "target_type": str,
                "details": str  # Human-readable explanation
            }
        """
        # Extract bone names
        source_bones = self._get_bone_names(source_skeleton)
        target_bones = self._get_bone_names(target_skeleton)
        
        # Get skeleton types
        source_type = source_skeleton.get('skeleton_type', 'unknown')
        target_type = target_skeleton.get('skeleton_type', 'unknown')
        
        logger.info(f"Checking compatibility: source={source_type}({len(source_bones)} bones), target={target_type}({len(target_bones)} bones)")
        
        # Normalize bone names for comparison
        source_normalized = self._normalize_bone_names(source_bones)
        target_normalized = self._normalize_bone_names(target_bones)
        
        # Find matches, missing, and extra bones
        matched_bones, missing_bones, extra_bones = self._compare_bone_sets(
            source_normalized,
            target_normalized
        )
        
        # Calculate compatibility score
        compatibility_score = self._calculate_compatibility_score(
            source_type,
            target_type,
            matched_bones,
            missing_bones,
            source_normalized
        )
        
        # Determine if compatible
        skeleton_type_match = (source_type == target_type) or (source_type == 'unknown' or target_type == 'unknown')
        is_compatible = (
            compatibility_score >= self.compatibility_threshold
            and (skeleton_type_match or source_type == 'other' or target_type == 'other')
        )
        
        # Generate detailed explanation
        details = self._generate_details(
            is_compatible,
            compatibility_score,
            source_type,
            target_type,
            matched_bones,
            missing_bones,
            extra_bones
        )
        
        result = {
            "compatible": is_compatible,
            "compatibility_score": round(compatibility_score, 3),
            "missing_bones": sorted(missing_bones),
            "extra_bones": sorted(extra_bones),
            "matched_bones": sorted(matched_bones),
            "skeleton_type_match": skeleton_type_match,
            "source_type": source_type,
            "target_type": target_type,
            "details": details
        }
        
        logger.info(f"Compatibility check result: compatible={is_compatible}, score={compatibility_score:.3f}")
        
        return result
    
    def _get_bone_names(self, skeleton: Dict) -> Set[str]:
        """
        Extract bone names from skeleton data.
        
        Args:
            skeleton: Skeleton data dictionary
        
        Returns:
            Set of bone names
        """
        bones = skeleton.get('bones', [])
        
        # Handle different formats
        if isinstance(bones, list):
            # List of bone dicts with 'name' field
            if bones and isinstance(bones[0], dict):
                return {bone.get('name', '') for bone in bones if bone.get('name')}
            # List of bone name strings
            elif bones and isinstance(bones[0], str):
                return set(bones)
        
        return set()
    
    def _normalize_bone_names(self, bone_names: Set[str]) -> Set[str]:
        """
        Normalize bone names for comparison (lowercase, remove special chars).
        
        Args:
            bone_names: Set of original bone names
        
        Returns:
            Set of normalized bone names
        """
        normalized = set()
        
        for name in bone_names:
            # Convert to lowercase and remove special characters
            normalized_name = name.lower().replace('_', '').replace('-', '').replace('.', '').replace(' ', '')
            normalized.add(normalized_name)
        
        return normalized
    
    def _compare_bone_sets(
        self,
        source_bones: Set[str],
        target_bones: Set[str]
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Compare source and target bone sets.
        
        Args:
            source_bones: Normalized source bone names
            target_bones: Normalized target bone names
        
        Returns:
            Tuple of (matched_bones, missing_bones, extra_bones)
        """
        if self.fuzzy_matching:
            # Use fuzzy matching with aliases
            matched_bones = set()
            missing_bones = set()
            
            for source_bone in source_bones:
                if self._fuzzy_match(source_bone, target_bones):
                    matched_bones.add(source_bone)
                else:
                    missing_bones.add(source_bone)
            
            # Find extra bones in target
            extra_bones = set()
            for target_bone in target_bones:
                if not self._fuzzy_match(target_bone, source_bones):
                    extra_bones.add(target_bone)
        else:
            # Exact matching
            matched_bones = source_bones & target_bones
            missing_bones = source_bones - target_bones
            extra_bones = target_bones - source_bones
        
        return matched_bones, missing_bones, extra_bones
    
    def _fuzzy_match(self, bone: str, bone_set: Set[str]) -> bool:
        """
        Check if a bone matches any bone in the set using fuzzy matching.
        
        Args:
            bone: Normalized bone name to match
            bone_set: Set of normalized bone names to search
        
        Returns:
            True if a match is found
        """
        # Direct match
        if bone in bone_set:
            return True
        
        # Check aliases
        for canonical_name, aliases in self.BONE_ALIASES.items():
            # Normalize canonical name and aliases
            canonical_normalized = canonical_name.lower().replace('_', '')
            aliases_normalized = [a.lower().replace('_', '') for a in aliases]
            
            # If bone matches canonical or any alias
            if bone == canonical_normalized or bone in aliases_normalized:
                # Check if any corresponding bone exists in target
                if canonical_normalized in bone_set:
                    return True
                for alias in aliases_normalized:
                    if alias in bone_set:
                        return True
        
        # Substring matching for common patterns
        # e.g., 'leftarm' should match 'left_upperarm'
        for target_bone in bone_set:
            if bone in target_bone or target_bone in bone:
                return True
        
        return False
    
    def _calculate_compatibility_score(
        self,
        source_type: str,
        target_type: str,
        matched_bones: Set[str],
        missing_bones: Set[str],
        source_bones: Set[str]
    ) -> float:
        """
        Calculate compatibility score based on bone matches.
        
        Args:
            source_type: Source skeleton type
            target_type: Target skeleton type
            matched_bones: Set of matched bone names
            missing_bones: Set of missing bone names
            source_bones: All source bone names
        
        Returns:
            Compatibility score (0-1)
        """
        if not source_bones:
            return 0.0
        
        # Base score: percentage of source bones found in target
        base_score = len(matched_bones) / len(source_bones)
        
        # Penalty for missing critical bones
        critical_missing_penalty = 0.0
        required_bones = self._get_required_bones(source_type)
        
        if required_bones:
            critical_missing = missing_bones & required_bones
            if critical_missing:
                # Penalize 0.1 per critical bone, up to 0.5 total
                critical_missing_penalty = min(0.5, len(critical_missing) * 0.1)
        
        # Bonus for skeleton type match
        type_bonus = 0.1 if source_type == target_type and source_type != 'unknown' else 0.0
        
        # Calculate final score
        final_score = max(0.0, base_score - critical_missing_penalty + type_bonus)
        final_score = min(1.0, final_score)  # Cap at 1.0
        
        return final_score
    
    def _get_required_bones(self, skeleton_type: str) -> Set[str]:
        """
        Get required bones for a skeleton type.
        
        Args:
            skeleton_type: 'humanoid', 'quadruped', or 'other'
        
        Returns:
            Set of required bone names (normalized)
        """
        if skeleton_type == 'humanoid':
            return self.HUMANOID_REQUIRED_BONES
        elif skeleton_type == 'quadruped':
            return self.QUADRUPED_REQUIRED_BONES
        else:
            return set()
    
    def _generate_details(
        self,
        is_compatible: bool,
        score: float,
        source_type: str,
        target_type: str,
        matched_bones: Set[str],
        missing_bones: Set[str],
        extra_bones: Set[str]
    ) -> str:
        """
        Generate human-readable compatibility details.
        
        Args:
            is_compatible: Whether skeletons are compatible
            score: Compatibility score
            source_type: Source skeleton type
            target_type: Target skeleton type
            matched_bones: Matched bone names
            missing_bones: Missing bone names
            extra_bones: Extra bone names
        
        Returns:
            Detailed explanation string
        """
        if is_compatible:
            if score >= 0.95:
                detail = f"Excellent match: {len(matched_bones)} bones matched between {source_type} source and {target_type} target."
            elif score >= 0.85:
                detail = f"Good match: {len(matched_bones)}/{len(matched_bones) + len(missing_bones)} source bones found in target."
            else:
                detail = f"Acceptable match: {len(matched_bones)} bones matched. Some bones may require approximation."
            
            if missing_bones:
                detail += f" {len(missing_bones)} minor bones missing: {', '.join(sorted(list(missing_bones))[:3])}{'...' if len(missing_bones) > 3 else ''}."
        else:
            if source_type != target_type and source_type != 'unknown' and target_type != 'unknown':
                detail = f"Incompatible: Source is {source_type} but target is {target_type}."
            elif score < 0.5:
                detail = f"Incompatible: Only {len(matched_bones)}/{len(matched_bones) + len(missing_bones)} bones matched (score: {score:.2f})."
            else:
                detail = f"Incompatible: Missing critical bones required for {source_type} retargeting."
            
            if missing_bones:
                critical_missing = self._get_critical_missing_bones(source_type, missing_bones)
                if critical_missing:
                    detail += f" Critical bones missing: {', '.join(sorted(list(critical_missing))[:5])}."
        
        return detail
    
    def _get_critical_missing_bones(self, skeleton_type: str, missing_bones: Set[str]) -> Set[str]:
        """
        Identify critical missing bones from the missing set.
        
        Args:
            skeleton_type: Skeleton type
            missing_bones: Set of missing bone names
        
        Returns:
            Set of critical missing bones
        """
        required_bones = self._get_required_bones(skeleton_type)
        return missing_bones & required_bones


def check_skeleton_compatibility(
    source_skeleton: Dict,
    target_skeleton: Dict,
    fuzzy_matching: bool = True,
    compatibility_threshold: float = 0.7
) -> Dict:
    """
    Convenience function to check skeleton compatibility.
    
    Args:
        source_skeleton: Source skeleton data (from motion clip)
        target_skeleton: Target skeleton data (from rigged model)
        fuzzy_matching: Enable fuzzy bone name matching
        compatibility_threshold: Minimum score to consider compatible
    
    Returns:
        Compatibility analysis dictionary
    """
    checker = SkeletonCompatibilityChecker(
        fuzzy_matching=fuzzy_matching,
        compatibility_threshold=compatibility_threshold
    )
    return checker.check_compatibility(source_skeleton, target_skeleton)
