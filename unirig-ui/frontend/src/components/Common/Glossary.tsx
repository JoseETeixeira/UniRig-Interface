import React, { useState } from 'react';
import { Modal } from './Modal';

interface GlossaryTerm {
  term: string;
  definition: string;
  category: string;
}

const GLOSSARY_TERMS: GlossaryTerm[] = [
  {
    term: 'Rigging',
    definition: 'The process of creating a skeletal structure and binding it to a 3D mesh so it can be animated.',
    category: '3D Concepts',
  },
  {
    term: 'Skeleton',
    definition: 'A hierarchical structure of bones and joints that defines how a 3D model can be posed and animated.',
    category: '3D Concepts',
  },
  {
    term: 'Skinning',
    definition: 'The process of assigning vertex weights to bones, determining how the mesh deforms when bones move.',
    category: '3D Concepts',
  },
  {
    term: 'Bone',
    definition: 'A single joint or limb in a skeleton hierarchy. Bones control the deformation of mesh vertices.',
    category: '3D Concepts',
  },
  {
    term: 'Weight Painting',
    definition: 'The manual process of assigning influence values to vertices to control how they deform with bones.',
    category: '3D Concepts',
  },
  {
    term: 'Mesh Topology',
    definition: 'The structure and arrangement of vertices, edges, and faces that make up a 3D model.',
    category: '3D Concepts',
  },
  {
    term: 'T-Pose / A-Pose',
    definition: 'Standard reference poses for humanoid models. T-pose has arms straight out, A-pose has arms at 45°.',
    category: '3D Concepts',
  },
  {
    term: 'FBX',
    definition: 'Filmbox format - A proprietary 3D file format by Autodesk, widely supported in game engines and 3D software.',
    category: 'File Formats',
  },
  {
    term: 'GLB',
    definition: 'Binary format of glTF (GL Transmission Format) - An open standard 3D file format optimized for web and real-time applications.',
    category: 'File Formats',
  },
  {
    term: 'OBJ',
    definition: 'Wavefront OBJ - A simple text-based 3D file format that stores geometry data.',
    category: 'File Formats',
  },
  {
    term: 'VRM',
    definition: 'Virtual Reality Model - A file format specifically designed for humanoid 3D avatars in VR applications.',
    category: 'File Formats',
  },
  {
    term: 'Random Seed',
    definition: 'A number that initializes the random number generator, ensuring reproducible results. Different seeds produce different skeletons.',
    category: 'Processing',
  },
  {
    term: 'Iteration Count',
    definition: 'The number of refinement passes during skinning generation. Higher counts produce smoother deformations but take longer.',
    category: 'Processing',
  },
  {
    term: 'CUDA',
    definition: 'NVIDIA\'s parallel computing platform for GPU acceleration. Required for fast model processing.',
    category: 'Technical',
  },
  {
    term: 'GPU',
    definition: 'Graphics Processing Unit - Specialized hardware for parallel computation, used to accelerate AI model inference.',
    category: 'Technical',
  },
  {
    term: 'Session',
    definition: 'A temporary workspace for your uploads and processing jobs. Sessions expire after 24 hours of inactivity.',
    category: 'Application',
  },
  {
    term: 'Job',
    definition: 'A processing task (upload, skeleton generation, skinning, or export) tracked by the system.',
    category: 'Application',
  },
];

interface GlossaryProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Glossary modal with searchable technical terms
 */
export const Glossary: React.FC<GlossaryProps> = ({ isOpen, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', ...Array.from(new Set(GLOSSARY_TERMS.map(t => t.category)))];

  const filteredTerms = GLOSSARY_TERMS.filter(term => {
    const matchesSearch = term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         term.definition.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || term.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="📖 Glossary" size="lg">
      <div>
        {/* Search and Filter */}
        <div className="mb-4 space-y-3">
          <input
            type="text"
            placeholder="Search terms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          <div className="flex flex-wrap gap-2">
            {categories.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`
                  px-3 py-1 rounded-md text-sm font-medium transition-colors
                  ${selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Terms List */}
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {filteredTerms.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No terms found matching "{searchQuery}"
            </p>
          ) : (
            filteredTerms.map(term => (
              <div key={term.term} className="pb-4 border-b border-gray-200 last:border-b-0">
                <div className="flex items-start justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">{term.term}</h3>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {term.category}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{term.definition}</p>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Can't find what you're looking for?{' '}
            <a
              href="https://github.com/VAST-AI-Research/UniRig"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline hover:no-underline"
            >
              View full documentation
            </a>
          </p>
        </div>
      </div>
    </Modal>
  );
};
