"""
Tests for skeleton compatibility detection.
"""

import pytest
from app.utils.skeleton_compatibility import (
    SkeletonCompatibilityChecker,
    check_skeleton_compatibility
)


class TestSkeletonCompatibilityChecker:
    """Test SkeletonCompatibilityChecker class."""
    
    def test_initialization_default(self):
        """Test default initialization."""
        checker = SkeletonCompatibilityChecker()
        assert checker.fuzzy_matching is True
        assert checker.compatibility_threshold == 0.7
    
    def test_initialization_custom(self):
        """Test custom initialization."""
        checker = SkeletonCompatibilityChecker(
            fuzzy_matching=False,
            compatibility_threshold=0.85
        )
        assert checker.fuzzy_matching is False
        assert checker.compatibility_threshold == 0.85


class TestGetBoneNames:
    """Test bone name extraction from skeleton data."""
    
    def test_get_bone_names_dict_list(self):
        """Test extraction from list of bone dictionaries."""
        checker = SkeletonCompatibilityChecker()
        skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'LeftArm'}
            ]
        }
        bone_names = checker._get_bone_names(skeleton)
        assert bone_names == {'Hips', 'Spine', 'LeftArm'}
    
    def test_get_bone_names_string_list(self):
        """Test extraction from list of bone name strings."""
        checker = SkeletonCompatibilityChecker()
        skeleton = {
            'bones': ['Hips', 'Spine', 'LeftArm']
        }
        bone_names = checker._get_bone_names(skeleton)
        assert bone_names == {'Hips', 'Spine', 'LeftArm'}
    
    def test_get_bone_names_empty(self):
        """Test extraction from empty skeleton."""
        checker = SkeletonCompatibilityChecker()
        skeleton = {'bones': []}
        bone_names = checker._get_bone_names(skeleton)
        assert bone_names == set()
    
    def test_get_bone_names_missing_key(self):
        """Test extraction when bones key is missing."""
        checker = SkeletonCompatibilityChecker()
        skeleton = {}
        bone_names = checker._get_bone_names(skeleton)
        assert bone_names == set()


class TestNormalizeBoneNames:
    """Test bone name normalization."""
    
    def test_normalize_lowercase(self):
        """Test conversion to lowercase."""
        checker = SkeletonCompatibilityChecker()
        names = {'LeftArm', 'RightLeg', 'SPINE'}
        normalized = checker._normalize_bone_names(names)
        assert 'leftarm' in normalized
        assert 'rightleg' in normalized
        assert 'spine' in normalized
    
    def test_normalize_remove_special_chars(self):
        """Test removal of special characters."""
        checker = SkeletonCompatibilityChecker()
        names = {'Left_Arm', 'Right-Leg', 'Spine.01', 'Head Bone'}
        normalized = checker._normalize_bone_names(names)
        assert 'leftarm' in normalized
        assert 'rightleg' in normalized
        assert 'spine01' in normalized
        assert 'headbone' in normalized


class TestExactMatching:
    """Test exact bone matching (no fuzzy matching)."""
    
    def test_exact_match_identical(self):
        """Test exact matching with identical bone sets."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=False)
        source_bones = {'hips', 'spine', 'leftarm'}
        target_bones = {'hips', 'spine', 'leftarm'}
        
        matched, missing, extra = checker._compare_bone_sets(source_bones, target_bones)
        
        assert matched == {'hips', 'spine', 'leftarm'}
        assert missing == set()
        assert extra == set()
    
    def test_exact_match_subset(self):
        """Test exact matching when target is subset of source."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=False)
        source_bones = {'hips', 'spine', 'leftarm', 'rightarm'}
        target_bones = {'hips', 'spine'}
        
        matched, missing, extra = checker._compare_bone_sets(source_bones, target_bones)
        
        assert matched == {'hips', 'spine'}
        assert missing == {'leftarm', 'rightarm'}
        assert extra == set()
    
    def test_exact_match_superset(self):
        """Test exact matching when target is superset of source."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=False)
        source_bones = {'hips', 'spine'}
        target_bones = {'hips', 'spine', 'leftarm', 'rightarm', 'tail'}
        
        matched, missing, extra = checker._compare_bone_sets(source_bones, target_bones)
        
        assert matched == {'hips', 'spine'}
        assert missing == set()
        assert extra == {'leftarm', 'rightarm', 'tail'}
    
    def test_exact_match_no_overlap(self):
        """Test exact matching with no overlapping bones."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=False)
        source_bones = {'bone1', 'bone2'}
        target_bones = {'bone3', 'bone4'}
        
        matched, missing, extra = checker._compare_bone_sets(source_bones, target_bones)
        
        assert matched == set()
        assert missing == {'bone1', 'bone2'}
        assert extra == {'bone3', 'bone4'}


class TestFuzzyMatching:
    """Test fuzzy bone matching with aliases."""
    
    def test_fuzzy_match_direct(self):
        """Test fuzzy matching with direct name match."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=True)
        assert checker._fuzzy_match('leftarm', {'leftarm', 'rightarm'}) is True
    
    def test_fuzzy_match_alias(self):
        """Test fuzzy matching with bone alias."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=True)
        # 'leftarm' should match 'lupperarm' or 'l_arm' via aliases
        assert checker._fuzzy_match('leftarm', {'larm', 'rightarm'}) is True
    
    def test_fuzzy_match_substring(self):
        """Test fuzzy matching with substring."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=True)
        # 'arm' is substring of 'leftarm'
        assert checker._fuzzy_match('arm', {'leftarm', 'rightarm'}) is True
    
    def test_fuzzy_match_no_match(self):
        """Test fuzzy matching with no match."""
        checker = SkeletonCompatibilityChecker(fuzzy_matching=True)
        assert checker._fuzzy_match('tail', {'hips', 'spine', 'head'}) is False


class TestCompatibilityScore:
    """Test compatibility score calculation."""
    
    def test_perfect_match_score(self):
        """Test score calculation for perfect match."""
        checker = SkeletonCompatibilityChecker()
        source_bones = {'hips', 'spine', 'leftarm', 'rightarm'}
        matched_bones = source_bones.copy()
        missing_bones = set()
        
        score = checker._calculate_compatibility_score(
            'humanoid', 'humanoid', matched_bones, missing_bones, source_bones
        )
        
        # Should be 1.0 (perfect match) + 0.1 (type bonus) = 1.0 (capped)
        assert score == 1.0
    
    def test_partial_match_score(self):
        """Test score calculation for partial match."""
        checker = SkeletonCompatibilityChecker()
        source_bones = {'hips', 'spine', 'leftarm', 'rightarm'}
        matched_bones = {'hips', 'spine'}
        missing_bones = {'leftarm', 'rightarm'}
        
        score = checker._calculate_compatibility_score(
            'humanoid', 'humanoid', matched_bones, missing_bones, source_bones
        )
        
        # Base: 2/4 = 0.5, type bonus: 0.1 = 0.6
        # Penalty for critical missing: 0.2 (2 critical bones * 0.1)
        # Final: 0.5 - 0.2 + 0.1 = 0.4
        assert 0.3 <= score <= 0.7  # Allow some flexibility
    
    def test_no_match_score(self):
        """Test score calculation for no match."""
        checker = SkeletonCompatibilityChecker()
        source_bones = {'bone1', 'bone2'}
        matched_bones = set()
        missing_bones = source_bones.copy()
        
        score = checker._calculate_compatibility_score(
            'humanoid', 'quadruped', matched_bones, missing_bones, source_bones
        )
        
        assert score < 0.5
    
    def test_empty_source_score(self):
        """Test score calculation for empty source."""
        checker = SkeletonCompatibilityChecker()
        score = checker._calculate_compatibility_score(
            'humanoid', 'humanoid', set(), set(), set()
        )
        assert score == 0.0


class TestCompatibilityCheck:
    """Test full compatibility check."""
    
    def test_compatible_humanoid_skeletons(self):
        """Test compatibility between two humanoid skeletons."""
        checker = SkeletonCompatibilityChecker(compatibility_threshold=0.7)
        
        source_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'Chest'},
                {'name': 'Neck'},
                {'name': 'Head'},
                {'name': 'LeftShoulder'},
                {'name': 'LeftArm'},
                {'name': 'LeftForeArm'},
                {'name': 'LeftHand'},
                {'name': 'RightShoulder'},
                {'name': 'RightArm'},
                {'name': 'RightForeArm'},
                {'name': 'RightHand'},
                {'name': 'LeftUpLeg'},
                {'name': 'LeftLeg'},
                {'name': 'LeftFoot'},
                {'name': 'RightUpLeg'},
                {'name': 'RightLeg'},
                {'name': 'RightFoot'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        target_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'Chest'},
                {'name': 'Neck'},
                {'name': 'Head'},
                {'name': 'Left_Shoulder'},
                {'name': 'Left_Arm'},
                {'name': 'Left_ForeArm'},
                {'name': 'Left_Hand'},
                {'name': 'Right_Shoulder'},
                {'name': 'Right_Arm'},
                {'name': 'Right_ForeArm'},
                {'name': 'Right_Hand'},
                {'name': 'Left_UpLeg'},
                {'name': 'Left_Leg'},
                {'name': 'Left_Foot'},
                {'name': 'Right_UpLeg'},
                {'name': 'Right_Leg'},
                {'name': 'Right_Foot'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        assert result['compatible'] is True
        assert result['compatibility_score'] >= 0.9
        assert result['skeleton_type_match'] is True
        assert len(result['matched_bones']) >= 15
    
    def test_incompatible_type_mismatch(self):
        """Test incompatibility due to skeleton type mismatch."""
        checker = SkeletonCompatibilityChecker(compatibility_threshold=0.7)
        
        source_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'Tail'}
            ],
            'skeleton_type': 'quadruped'
        }
        
        target_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'Head'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        assert result['skeleton_type_match'] is False
        assert result['source_type'] == 'quadruped'
        assert result['target_type'] == 'humanoid'
    
    def test_incompatible_missing_bones(self):
        """Test incompatibility due to missing critical bones."""
        checker = SkeletonCompatibilityChecker(compatibility_threshold=0.7)
        
        source_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'LeftArm'},
                {'name': 'RightArm'},
                {'name': 'LeftLeg'},
                {'name': 'RightLeg'},
                {'name': 'Head'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        target_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        assert result['compatible'] is False
        assert result['compatibility_score'] < 0.7
        assert len(result['missing_bones']) >= 3
    
    def test_compatible_with_extra_bones(self):
        """Test compatibility when target has extra bones."""
        checker = SkeletonCompatibilityChecker(compatibility_threshold=0.7)
        
        source_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'Head'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        target_skeleton = {
            'bones': [
                {'name': 'Hips'},
                {'name': 'Spine'},
                {'name': 'Head'},
                {'name': 'LeftFinger1'},
                {'name': 'LeftFinger2'},
                {'name': 'RightFinger1'},
                {'name': 'RightFinger2'}
            ],
            'skeleton_type': 'humanoid'
        }
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        # Should be compatible (all source bones present)
        assert result['compatible'] is True
        assert len(result['extra_bones']) == 4
        assert len(result['matched_bones']) == 3


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_check_skeleton_compatibility_function(self):
        """Test convenience function works correctly."""
        source_skeleton = {
            'bones': ['Hips', 'Spine', 'Head'],
            'skeleton_type': 'humanoid'
        }
        
        target_skeleton = {
            'bones': ['Hips', 'Spine', 'Head'],
            'skeleton_type': 'humanoid'
        }
        
        result = check_skeleton_compatibility(source_skeleton, target_skeleton)
        
        assert 'compatible' in result
        assert 'compatibility_score' in result
        assert 'missing_bones' in result
        assert 'extra_bones' in result
        assert 'matched_bones' in result
        assert result['compatible'] is True


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_source_skeleton(self):
        """Test with empty source skeleton."""
        checker = SkeletonCompatibilityChecker()
        
        source_skeleton = {'bones': []}
        target_skeleton = {'bones': ['Hips', 'Spine']}
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        assert result['compatible'] is False
        assert result['compatibility_score'] == 0.0
    
    def test_empty_target_skeleton(self):
        """Test with empty target skeleton."""
        checker = SkeletonCompatibilityChecker()
        
        source_skeleton = {'bones': ['Hips', 'Spine']}
        target_skeleton = {'bones': []}
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        assert result['compatible'] is False
        assert len(result['missing_bones']) == 2
    
    def test_both_skeletons_empty(self):
        """Test with both skeletons empty."""
        checker = SkeletonCompatibilityChecker()
        
        source_skeleton = {'bones': []}
        target_skeleton = {'bones': []}
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        assert result['compatibility_score'] == 0.0
    
    def test_unknown_skeleton_types(self):
        """Test with unknown skeleton types."""
        checker = SkeletonCompatibilityChecker()
        
        source_skeleton = {
            'bones': ['BoneA', 'BoneB', 'BoneC'],
            'skeleton_type': 'unknown'
        }
        
        target_skeleton = {
            'bones': ['BoneA', 'BoneB', 'BoneC'],
            'skeleton_type': 'unknown'
        }
        
        result = checker.check_compatibility(source_skeleton, target_skeleton)
        
        # Should still work with unknown types
        assert 'compatible' in result
        assert result['skeleton_type_match'] is True


class TestDetailsGeneration:
    """Test human-readable details generation."""
    
    def test_details_excellent_match(self):
        """Test details for excellent match."""
        checker = SkeletonCompatibilityChecker()
        
        details = checker._generate_details(
            is_compatible=True,
            score=0.98,
            source_type='humanoid',
            target_type='humanoid',
            matched_bones={'bone1', 'bone2', 'bone3'},
            missing_bones=set(),
            extra_bones=set()
        )
        
        assert 'Excellent match' in details
        assert 'humanoid' in details
    
    def test_details_incompatible_type_mismatch(self):
        """Test details for incompatible type mismatch."""
        checker = SkeletonCompatibilityChecker()
        
        details = checker._generate_details(
            is_compatible=False,
            score=0.5,
            source_type='humanoid',
            target_type='quadruped',
            matched_bones={'bone1'},
            missing_bones={'bone2', 'bone3'},
            extra_bones=set()
        )
        
        assert 'Incompatible' in details
        assert 'humanoid' in details
        assert 'quadruped' in details
    
    def test_details_missing_critical_bones(self):
        """Test details when critical bones are missing."""
        checker = SkeletonCompatibilityChecker()
        
        missing_bones = {'hips', 'spine', 'leftarm', 'rightarm'}
        
        details = checker._generate_details(
            is_compatible=False,
            score=0.3,
            source_type='humanoid',
            target_type='humanoid',
            matched_bones={'head'},
            missing_bones=missing_bones,
            extra_bones=set()
        )
        
        assert 'Incompatible' in details or 'Critical' in details


class TestRequiredBones:
    """Test required bones identification."""
    
    def test_humanoid_required_bones(self):
        """Test humanoid required bones."""
        checker = SkeletonCompatibilityChecker()
        required = checker._get_required_bones('humanoid')
        
        assert 'hips' in required
        assert 'spine' in required
        assert 'leftshoulder' in required
        assert 'leftupleg' in required
    
    def test_quadruped_required_bones(self):
        """Test quadruped required bones."""
        checker = SkeletonCompatibilityChecker()
        required = checker._get_required_bones('quadruped')
        
        assert 'hips' in required
        assert 'tail' in required
        assert 'frontleftleg' in required
    
    def test_other_required_bones(self):
        """Test other skeleton type has no required bones."""
        checker = SkeletonCompatibilityChecker()
        required = checker._get_required_bones('other')
        
        assert len(required) == 0
    
    def test_unknown_required_bones(self):
        """Test unknown skeleton type has no required bones."""
        checker = SkeletonCompatibilityChecker()
        required = checker._get_required_bones('unknown')
        
        assert len(required) == 0
