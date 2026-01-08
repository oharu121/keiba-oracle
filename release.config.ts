import { defineConfig } from 'release-police';

export default defineConfig({
  // Branches that allow releases
  releaseBranches: ['main', 'master'],

  // Commands to run during release
  commands: {
    test: 'npm test',  // Set to null to skip
    install: 'npm install',    // Run after pulling changes
    build: null,               // Optional: run before version bump
    changelog: null,           // Optional: generate changelog
  },

  // Git settings
  git: {
    pullStrategy: 'rebase',        // 'rebase' | 'merge' | 'ff-only'
    requireCleanWorkingDir: true,
  },

  // GitHub integration (optional)
  github: {
    release: false,        // Create GitHub release after push
    draft: true,           // Create as draft (recommended)
    generateNotes: true,   // Auto-generate release notes
  },

  // Enable/disable steps
  steps: {
    checkBranch: true,
    syncRemote: true,
    runTests: true,
    commitChanges: true,
    versionBump: true,
    push: true,
    githubRelease: false,
  },
});
