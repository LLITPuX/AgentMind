'use client';

import React, { useState } from 'react';
import { addObservation, triggerConsolidation, searchMemory } from '../services/api';
import styles from './InteractionPanel.module.css';

interface InteractionPanelProps {
    onConsolidationStart: () => void;
    onConsolidationComplete: (result: any) => void;
    onSearchResult: (result: any) => void;
    onStmUpdate: (newSize: number) => void;
}

const InteractionPanel: React.FC<InteractionPanelProps> = ({
    onConsolidationStart,
    onConsolidationComplete,
    onSearchResult,
    onStmUpdate,
}) => {
    const [observation, setObservation] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleAddObservation = async () => {
        if (!observation.trim()) return;
        setIsLoading(true);
        try {
            const result = await addObservation(observation);
            onStmUpdate(result.stm_size);
            setObservation('');
        } catch (error) {
            console.error('Failed to add observation:', error);
            // Here you could add a toast notification for the user
        }
        setIsLoading(false);
    };

    const handleConsolidate = async () => {
        setIsLoading(true);
        onConsolidationStart();
        try {
            const result = await triggerConsolidation();
            onConsolidationComplete(result);
        } catch (error) {
            console.error('Failed to trigger consolidation:', error);
        }
        setIsLoading(false);
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setIsLoading(true);
        try {
            const result = await searchMemory(searchQuery);
            onSearchResult(result);
        } catch (error) {
            console.error('Failed to search memory:', error);
        }
        setIsLoading(false);
    };

    return (
        <div className={styles.panel}>
            {/* Observation Section */}
            <div className={styles.section}>
                <h3 className={styles.title}>Add Observation (STM)</h3>
                <textarea
                    className={styles.textarea}
                    value={observation}
                    onChange={(e) => setObservation(e.target.value)}
                    placeholder="Enter a new fact or observation..."
                    disabled={isLoading}
                />
                <button
                    className={styles.button}
                    onClick={handleAddObservation}
                    disabled={isLoading || !observation.trim()}
                >
                    {isLoading ? 'Adding...' : 'Add to STM'}
                </button>
            </div>

            {/* Consolidation Section */}
            <div className={styles.section}>
                <h3 className={styles.title}>Consolidate Memory</h3>
                <p className={styles.description}>
                    Process observations from STM and integrate them into the LTM knowledge graph.
                </p>
                <button className={styles.button} onClick={handleConsolidate} disabled={isLoading}>
                    {isLoading ? 'Consolidating...' : 'Run Consolidation'}
                </button>
            </div>

            {/* Search Section */}
            <div className={styles.section}>
                <h3 className={styles.title}>Search Memory (LTM)</h3>
                <input
                    type="text"
                    className={styles.input}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Ask a question to the agent..."
                    disabled={isLoading}
                />
                <button
                    className={styles.button}
                    onClick={handleSearch}
                    disabled={isLoading || !searchQuery.trim()}
                >
                    {isLoading ? 'Searching...' : 'Search'}
                </button>
            </div>
        </div>
    );
};

export default InteractionPanel;
