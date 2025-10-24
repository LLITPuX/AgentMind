'use client';

import React from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { GraphData } from '../services/api';

interface GraphVisualizerProps {
    graphData: GraphData;
}

const GraphVisualizer: React.FC<GraphVisualizerProps> = ({ graphData }) => {
    
    if (!graphData || !graphData.nodes || !graphData.links) {
        return <div>Loading graph data...</div>;
    }
    
    return (
        <ForceGraph2D
            graphData={graphData}
            nodeLabel="id"
            nodeAutoColorBy="group"
            linkDirectionalParticles={1}
            linkDirectionalParticleWidth={1.5}
            width={800}
            height={600}
        />
    );
};

export default GraphVisualizer;
