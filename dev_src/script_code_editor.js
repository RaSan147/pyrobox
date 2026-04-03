/**
 * Lightweight Code Editor Page - Highly optimized
 * Features:
 * - Syntax highlighting via CodeMirror 5 (lightweight)
 * - Auto-detect language from file extension
 * - Find & Replace (Ctrl+F, Ctrl+H)
 * - Undo/Redo
 * - Unsaved changes alert
 * - Large file warning (> 4MB)
 * - Truncated display for read-only large files (16KB preview)
 * - Conflict detection
 * - Minimal bloat, maximum performance
 */

class CodeEditor_Page extends Page {
	constructor(controller = page_controller, type = "code", handle_part = "code-editor-page") {
		super(controller, type, handle_part);

		this.editor_container = byId("editor-container");
		this.editor_header = byId("editor-header");
		this.sticky_header = byId("editor-sticky-header");
		this.file_title = byId("editor-file-title");
		this.file_info = byId("editor-file-info");
		this.save_btn = byId("editor-save-btn");
		this.download_btn = byId("editor-download-btn");
		this.readonly_toggle_btn = byId("editor-toggle-readonly-btn");
		this.password_input = byId("editor-password-input");
		this.line_ending_select = byId("editor-line-ending-select");
		this.unsaved_indicator = byId("editor-unsaved-indicator");

		this.password_cached = null; // Cache password after first successful save
		this.current_line_ending = 'LF'; // Default line ending

		this.editor = null;
		this.current_file_path = null;
		this.current_mod_time = null;
		this.is_modified = false;
		this.is_read_only = false;
		this.is_truncated = false;
		this.is_fallback = typeof CodeMirror === 'undefined';
		this.current_language = 'null';
		this.file_size = 0;

		// Bind Topbar offset scroll tracking
		top_bar.on_change((is_visible) => {
			this.sticky_header.style.top = is_visible ? '50px' : '0px';
		});

		// Store listener references for cleanup
		this.beforeunload_listener = (e) => {
			if (this.is_modified && !this.is_read_only) {
				e.preventDefault();
				e.returnValue = '';
				return '';
			}
		};
		this.change_listener = () => {
			if (!this.is_modified) {
				this.is_modified = true;
				this.update_unsaved_indicator();
			}
		};
		this.save_listener = () => this.save_file();
		this.find_panel_listeners = []; // Track find/replace listeners for cleanup
		this.pending_timeouts = []; // Track timeouts for cleanup
		this.is_active = true; // Flag to track if handler is still active

		// Initialize CodeMirror with minimal config
		if (!this.is_fallback) {
			try {
				this.editor = CodeMirror(this.editor_container, {
					value: "Loading...",
					mode: "null",
					theme: "default",
					lineNumbers: true,
					lineWrapping: true,
					indentUnit: 4,
					tabSize: 4,
					indentWithTabs: false,
					matchBrackets: true,
					autoCloseBrackets: true,
					matchTags: {bothTags: true},
					foldGutter: true,
					gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
					styleActiveLine: true,
					readOnly: false,
					electricChars: false,
					// Keyboard shortcuts
					extraKeys: {
						"Ctrl-S": () => this.save_file(),
						"Cmd-S": () => this.save_file(),
						"Ctrl-F": () => this.toggle_find_replace(),
						"Cmd-F": () => this.toggle_find_replace(),
						"Ctrl-H": () => this.toggle_find_replace(true),
						"Cmd-H": () => this.toggle_find_replace(true),
					}
				});

				// Listen for content changes (stored for cleanup)
				this.editor.on('change', this.change_listener);

				// Add search/replace functionality
				this.setup_find_replace();
			} catch (e) {
				console.error("Failed to initialize CodeMirror:", e);
				this.editor = null;
			}
		}

		// Setup event listeners (stored for cleanup)
		this.save_btn.addEventListener('click', this.save_listener);

		// Download button listener
		const download_listener = () => this.download_file();
		this.download_btn.addEventListener('click', download_listener);
		this.find_panel_listeners.push({ element: this.download_btn, type: 'click', handler: download_listener });

		// Read-only toggle button listener
		const readonly_listener = () => this.toggle_readonly();
		this.readonly_toggle_btn.addEventListener('click', readonly_listener);
		this.find_panel_listeners.push({ element: this.readonly_toggle_btn, type: 'click', handler: readonly_listener });

		// Warn on unsaved changes before leaving (stored for cleanup)
		window.addEventListener('beforeunload', this.beforeunload_listener);
	}

	setup_find_replace() {
		// Create find/replace panel
		const panel = document.createElement('div');
		panel.id = 'editor-find-panel';
		panel.className = 'editor-find-panel hidden';
		panel.innerHTML = `
			<div class="find-controls">
				<input type="text" id="find-input" placeholder="Find..." class="find-input">
				<input type="text" id="replace-input" placeholder="Replace..." class="find-input" style="display:none;">
				<button id="find-prev-btn" class="find-btn" title="Find Previous (Shift+F3 / F4)"><span class="fa fa-solid fa-arrow-up">↑</span></button>
				<button id="find-next-btn" class="find-btn" title="Find Next (F3)"><span class="fa fa-solid fa-arrow-down">↓</span></button>
				<button id="replace-btn" class="find-btn" style="display:none;" title="Replace">Replace</button>
				<button id="replace-all-btn" class="find-btn" style="display:none;" title="Replace All">Replace All</button>
				<button id="toggle-replace-btn" class="find-btn" title="Toggle Replace"><span class="fa fa-solid fa-retweet">⇅</span></button>
				<button id="close-find-btn" class="find-btn" title="Close (Esc)"><span class="fa fa-solid fa-times">✕</span></button>
				<span id="find-status" class="find-status"></span>
			</div>
		`;
		
		const stickyHeader = document.getElementById('editor-sticky-header');
		if (stickyHeader) {
			stickyHeader.appendChild(panel);
		} else {
			this.editor_container.parentElement.insertBefore(panel, this.editor_container);
		}

		// Run font awesome swapper on the new elements if it exists
		theme_controller.del_fa_alt();

		const find_input = byId('find-input');
		const replace_input = byId('replace-input');
		const replace_btn = byId('replace-btn');
		const replace_all_btn = byId('replace-all-btn');
		const toggle_replace_btn = byId('toggle-replace-btn');
		const close_find_btn = byId('close-find-btn');
		const find_next_btn = byId('find-next-btn');
		const find_prev_btn = byId('find-prev-btn');
		const find_status = byId('find-status');

		// Search state
		const search_state = {
			query: '',
			index: 0,
			matches: []
		};

		const update_search = () => {
			if (!this.editor) return;

			const query = find_input.value;
			search_state.query = query;
			search_state.matches = [];

			if (!query) {
				this.editor.clearSearch();
				find_status.innerText = '';
				return;
			}

			// Simple search implementation
			const content = this.editor.getValue();
			const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
			let match;
			while ((match = regex.exec(content)) !== null) {
				search_state.matches.push({
					start: match.index,
					end: match.index + match[0].length,
					text: match[0]
				});
			}

			find_status.innerText = search_state.matches.length > 0
				? `${search_state.matches.length} matches`
				: 'No matches';

			search_state.index = 0;
			highlight_match(0);
		};

		const highlight_match = (index) => {
			if (!search_state.matches[index]) return;

			// Temporarily disable the global top_bar auto-hide during programmatic scrolls
			top_bar.dont_move = true;
			clearTimeout(this._scroll_timeout);
			this._scroll_timeout = setTimeout(() => {
				// Re-sync so the sudden jump in scroll math doesn't pop the bar open
				top_bar.prevScrollpos = window.scrollY;
				top_bar.dont_move = false;
			}, 50); // 50ms ensures instant jump completes
			this.pending_timeouts.push(this._scroll_timeout);

			const match = search_state.matches[index];
			const start = this.editor.posFromIndex(match.start);
			const end = this.editor.posFromIndex(match.end);

			this.editor.setSelection(start, end);
			this.editor.scrollIntoView({ line: start.line, ch: start.ch });
			
			search_state.index = index;
		};

		const keydown_handler = (e) => {
			if (e.key === 'Enter') {
				e.preventDefault();
				e.shiftKey ? prev_handler() : next_handler();
			}
		};
		find_input.addEventListener('keydown', keydown_handler);
		this.find_panel_listeners.push({ element: find_input, type: 'keydown', handler: keydown_handler });

		const next_handler = () => {
			if (find_input.value !== search_state.query) {
				update_search();
				return;
			}
			if (search_state.matches.length > 0) {
				const next_index = (search_state.index + 1) % search_state.matches.length;
				highlight_match(next_index);
			}
		};
		find_next_btn.addEventListener('click', next_handler);
		this.find_panel_listeners.push({ element: find_next_btn, type: 'click', handler: next_handler });

		const prev_handler = () => {
			if (find_input.value !== search_state.query) {
				update_search();
				return;
			}
			if (search_state.matches.length > 0) {
				const prev_index = (search_state.index - 1 + search_state.matches.length) % search_state.matches.length;
				highlight_match(prev_index);
			}
		};
		find_prev_btn.addEventListener('click', prev_handler);
		this.find_panel_listeners.push({ element: find_prev_btn, type: 'click', handler: prev_handler });

		// Global F3/F4 hotkeys
		const global_hotkey_handler = (e) => {
			if (e.key === 'F3') {
				e.preventDefault();
				e.shiftKey ? prev_handler() : next_handler();
			} else if (e.key === 'F4') {
				e.preventDefault();
				prev_handler();
			}
		};
		window.addEventListener('keydown', global_hotkey_handler);
		this.find_panel_listeners.push({ element: window, type: 'keydown', handler: global_hotkey_handler });

		const toggle_handler = () => {
			const show = replace_input.style.display === 'none';
			replace_input.style.display = show ? 'block' : 'none';
			replace_btn.style.display = show ? 'block' : 'none';
			replace_all_btn.style.display = show ? 'block' : 'none';
			if (show) replace_input.focus();
		};
		toggle_replace_btn.addEventListener('click', toggle_handler);
		this.find_panel_listeners.push({ element: toggle_replace_btn, type: 'click', handler: toggle_handler });

		const replace_handler = () => {
			if (find_input.value !== search_state.query) {
				update_search();
			}
			if (!search_state.matches[search_state.index]) return;

			const match = search_state.matches[search_state.index];
			const start = this.editor.posFromIndex(match.start);
			const end = this.editor.posFromIndex(match.end);

			this.editor.replaceRange(replace_input.value, start, end);
			this.is_modified = true;
			this.update_unsaved_indicator();
			update_search();
		};
		replace_btn.addEventListener('click', replace_handler);
		this.find_panel_listeners.push({ element: replace_btn, type: 'click', handler: replace_handler });

		const replace_all_handler = () => {
			if (find_input.value !== search_state.query) {
				update_search();
			}
			if (!search_state.matches.length) return;

			// Replace from end to start to maintain indices
			for (let i = search_state.matches.length - 1; i >= 0; i--) {
				const match = search_state.matches[i];
				const start = this.editor.posFromIndex(match.start);
				const end = this.editor.posFromIndex(match.end);
				this.editor.replaceRange(replace_input.value, start, end);
			}

			this.is_modified = true;
			this.update_unsaved_indicator();
			update_search();
			this.show_status(`Replaced ${search_state.matches.length} occurrences`, 'success');
		};
		replace_all_btn.addEventListener('click', replace_all_handler);
		this.find_panel_listeners.push({ element: replace_all_btn, type: 'click', handler: replace_all_handler });

		const close_handler = () => {
			this.toggle_find_replace();
		};
		close_find_btn.addEventListener('click', close_handler);
		this.find_panel_listeners.push({ element: close_find_btn, type: 'click', handler: close_handler });

		// Expose for showing
		this.find_panel = panel;
		this.find_input = find_input;
	}

	toggle_find_replace(show_replace = false) {
		if (!this.find_panel) return;

		const is_hidden = this.find_panel.classList.contains('hidden');
		if (is_hidden) {
			this.find_panel.classList.remove('hidden');
			this.find_input.focus();
			if (show_replace) {
				byId('replace-input').style.display = 'block';
				byId('replace-btn').style.display = 'block';
				byId('replace-all-btn').style.display = 'block';
			}
		} else {
			this.find_panel.classList.add('hidden');
			if (this.editor) this.editor.focus();
		}
	}



	async initialize() {
		// Reset active flag when initializing (coming back to this handler)
		this.is_active = true;

		this.controller.show_actions_button();
		this.controller.set_actions_button_text("Tools", { class: "fa-solid fa-wrench", text: "🛠" });

		this.controller.set_action_tools([
			{
				text: "Find & Replace",
				icon_class: "fa-solid fa-magnifying-glass",
				icon_text: "🔍",
				action: () => this.toggle_find_replace()
			},
			{
				text: "Reload File",
				icon_class: "fa-solid fa-arrows-rotate",
				icon_text: "🔄",
				action: () => this.initialize()
			}
		]);

		// Get file data from server
		try {
			const url = tools.add_query_here("edit-data");
			const response = await fetch(url);

			// Check if still active after async call
			if (!this.is_active) return;

			if (!response.ok) {
				if (response.status === 401) {
					this.show_status("Authentication required", "error");
					return;
				}
				const error_data = await response.json();
				this.show_status(error_data.message || "Failed to load file", "error");
				return;
			}

			const data = await response.json();

			// Check if still active after async call
			if (!this.is_active) return;

			if (data.status !== "success") {
				this.show_status(data.message || "Failed to load file", "error");
				return;
			}

			// Load file data
			this.current_file_path = data.path;
			this.current_mod_time = data.mod_time;
			this.current_line_ending = data.line_ending || 'LF'; // Store detected line ending
			this.user_can_edit = data.can_edit; // User has permission to edit
			this.is_read_only = true; // Initialize to read-only by default to prevent accidental edits
			this.is_truncated = data.is_truncated;
			this.current_language = data.language;
			this.file_size = data.file_size;

			// Set line ending selector to match file
			this.line_ending_select.value = this.current_line_ending;

			this.set_title(data.file_name);
			this.file_title.innerText = data.file_name;

			// Show file info with size
			let info_text = this.format_file_size(data.file_size) + ' • ' + this.current_language;
			if (data.is_truncated) {
				info_text += ' • PREVIEW (16KB)';
			}
			this.file_info.innerText = info_text;

			// Enable download button now that file is loaded
			this.download_btn.disabled = false;

			// Set editor content and language
			if (!this.is_fallback) {
				this.editor.setValue(data.content);
				this.set_editor_language(data.language);
				this.is_modified = false;
				this.update_unsaved_indicator();

				this.editor.clearHistory();
				// refresh after layout is settled
				setTimeout(() => this.editor.refresh(), 50);

				// Handle file size warnings and permissions
				if (data.is_truncated) {
					// Show warning for very large files
					this.show_status(`⚠️ File is ${this.format_file_size(data.file_size)} - showing first 16KB preview only. Download to view entire file.`, 'warning');
					this.editor.setOption("readOnly", true);
					this.save_btn.disabled = true;
				} else if (data.file_size > 1024 * 1024) {
					// Warn for files > 1MB but editable
					this.show_status(`⚠️ File is ${this.format_file_size(data.file_size)} - may be slow to edit`, 'warning');
				}

				// Set read-only mode if needed
				if (!this.user_can_edit && !data.is_truncated) {
					this.editor.setOption("readOnly", true);
					this.save_btn.disabled = true;
					this.readonly_toggle_btn.disabled = true;
					this.update_readonly_button_state();
					this.show_status("Read-only mode (no modify permission)", "info");
				} else if (data.is_truncated) {
					// Very large files are always read-only
					this.editor.setOption("readOnly", true);
					this.save_btn.disabled = true;
					this.readonly_toggle_btn.disabled = true;
					this.update_readonly_button_state();
					this.show_status("Read-only mode (file too large)", "info");
				} else {
					this.editor.setOption("readOnly", false); // explicitly re-enable otherwise a previous file's state persists
					this.editor.setOption("readOnly", true); // explicitly start read-only for safety
					this.save_btn.disabled = true;
					this.readonly_toggle_btn.disabled = false;
					this.update_readonly_button_state();
					this.show_status("Press Ctrl+F to search, or click Enable Editing to modify.", "success");
				}
			} else {
				// Fallback if CodeMirror not available - create offline editor with line numbers
				// We reconstruct it completely inplace to ensure payload displays visibly
				this.create_fallback_editor(data);
				this.is_modified = false;
				this.update_unsaved_indicator();
				
				if (!this.user_can_edit || data.is_truncated) {
					this.save_btn.disabled = true;
					this.readonly_toggle_btn.disabled = true;
				} else {
					this.save_btn.disabled = true; // wait for unlock
					this.readonly_toggle_btn.disabled = false;
				}
			}

	} catch (error) {
		if (!this.is_active) return;
		console.error("Error loading file:", error);
		this.show_status("Error loading file: " + error.message, "error");
	}
}

	set_editor_language(language) {
		const mode_map = {
			'python': 'python',
			'javascript': 'javascript',
			'html': 'htmlmixed',
			'css': 'css',
			'json': 'application/json',
			'xml': 'application/xml',
			'markdown': 'markdown',
			'sql': 'text/x-sql',
			'java': 'text/x-java',
			'cpp': 'text/x-c++src',
			'c': 'text/x-csrc',
			'go': 'text/x-go',
			'php': 'application/x-httpd-php',
			'ruby': 'text/x-ruby',
			'yaml': 'text/x-yaml',
			'shell': 'application/x-sh',
			'groovy': 'text/x-groovy',
			'toml': 'text/x-toml',
			'r': 'text/x-rsrc',
			'null': null
		};

		const mode = mode_map[language] || null;
		if (mode) {
			try {
				this.editor.setOption("mode", mode);
			} catch (e) {
				console.warn(`Could not set mode for ${language}:`, e);
				// Fall back to null mode
				this.editor.setOption("mode", null);
			}
		}
	}

	create_fallback_editor(data) {
		// Clean up previous instances safely
		tools.del_child(this.editor_container);

		// Clear inline styles to rely purely on CSS .editor-container properties
		this.editor_container.style.display = 'flex';
		this.editor_container.style.flexDirection = 'column';
		this.editor_container.style.position = 'relative';
		this.editor_container.style.height = '100%';

		// Content display
		const content_display = data.is_truncated
			? `[PREVIEW - First 16KB of ${this.format_file_size(data.file_size)} file]\n\n${data.content}`
			: data.content;

		// Create editor wrapper
		const wrapper = document.createElement('div');
		wrapper.className = "fallback-editor-wrapper";
		wrapper.style.display = 'flex';
		wrapper.style.flexDirection = 'row';
		wrapper.style.flexGrow = '1';
		wrapper.style.width = '100%';
		wrapper.style.overflow = 'hidden';
		wrapper.style.backgroundColor = '#1e1e1e';
		wrapper.style.color = '#e0e0e0';

		// Create line numbers column
		const line_numbers = document.createElement('div');
		line_numbers.className = "fallback-line-numbers";
		line_numbers.style.width = '45px';
		line_numbers.style.minWidth = '45px';
		line_numbers.style.boxSizing = 'border-box';
		line_numbers.style.backgroundColor = '#252526';
		line_numbers.style.borderRight = '1px solid #3e3e42';
		line_numbers.style.padding = '10px 5px';
		line_numbers.style.paddingBottom = '50vh';
		line_numbers.style.textAlign = 'right';
		line_numbers.style.userSelect = 'none';
		line_numbers.style.fontFamily = "monospace";
		line_numbers.style.fontSize = '14px';
		line_numbers.style.lineHeight = '1.5';
		line_numbers.style.color = '#858585';
		line_numbers.style.overflow = 'hidden';
		line_numbers.style.whiteSpace = 'pre-wrap';

		// Create textarea
		const textarea = document.createElement('textarea');
		textarea.className = "fallback-textarea";
		textarea.setAttribute('wrap', 'off');
		textarea.setAttribute('spellcheck', 'false');
		textarea.textContent = content_display; // Write content visibly to DOM so tools like DarkReader don't collapse empty inputs
		textarea.value = content_display; 

		textarea.style.flexGrow = '1';
		textarea.style.width = '100%';
		textarea.style.boxSizing = 'border-box';
		textarea.style.padding = '10px';
		textarea.style.paddingBottom = '50vh';
		textarea.style.margin = '0';
		textarea.style.fontFamily = "monospace";
		textarea.style.fontSize = '14px';
		textarea.style.lineHeight = '1.5';
		textarea.style.backgroundColor = 'transparent'; // Inheriting background and color solves conflicts
		textarea.style.color = 'inherit';
		textarea.style.border = 'none';
		textarea.style.outline = 'none';
		textarea.style.resize = 'none';
		textarea.style.whiteSpace = 'pre';
		textarea.style.overflow = 'auto hidden';

		// Add elements
		wrapper.appendChild(line_numbers);
		wrapper.appendChild(textarea);
		this.editor_container.appendChild(wrapper);

		const update_line_numbers = () => {
			const linesCount = textarea.value.split('\n').length;
			let numbers = '';
			for (let i = 1; i <= linesCount; i++) {
				numbers += i + '\n';
			}
			line_numbers.textContent = numbers;
		};

		// Sync scroll
		textarea.addEventListener('scroll', () => {
			line_numbers.scrollTop = textarea.scrollTop;
		});

		// Event tracking
		textarea.addEventListener('input', () => {
			if (!this.is_modified) {
				this.is_modified = true;
				this.update_unsaved_indicator();
			}
			update_line_numbers();
		});

		textarea.addEventListener('keydown', (e) => {
			if ((e.ctrlKey || e.metaKey) && e.key === 's') {
				e.preventDefault();
				this.save_file();
			}
			if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
				e.preventDefault();
				this.toggle_find_replace();
			}
			if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
				e.preventDefault();
				this.toggle_find_replace(true);
			}
			if (e.key === 'Tab') {
				e.preventDefault();
				const start = textarea.selectionStart;
				const end = textarea.selectionEnd;
				textarea.value = textarea.value.substring(0, start) + '\t' + textarea.value.substring(end);
				textarea.selectionStart = textarea.selectionEnd = start + 1;
				textarea.dispatchEvent(new Event('input'));
			}
		});

		// Build Fallback API to avoid CodeMirror crashes
		this.is_fallback = true;
		this.editor = {
			focus: () => textarea.focus(),
			getValue: () => textarea.value,
			setValue: (val) => {
				textarea.value = val !== undefined ? val : "";
				textarea.textContent = val !== undefined ? val : ""; // Sync devtools dom visual
				update_line_numbers();
			},
			setOption: (key, val) => {
				if (key === "readOnly") {
					textarea.readOnly = val;
					textarea.style.opacity = val ? '0.7' : '1';
				}
			},
			clearHistory: () => {},
			refresh: () => update_line_numbers(),
			
			// Mock Find & Replace specific APIs to bind to Textarea natively
			clearSearch: () => {},
			posFromIndex: (index) => {
				const lines = textarea.value.substring(0, index).split('\n');
				return { index, line: lines.length - 1, ch: lines[lines.length - 1].length };
			},
			setSelection: (start, end) => {
				textarea.focus({ preventScroll: true });
				textarea.setSelectionRange(start.index, end.index);
			},
			scrollIntoView: (pos) => {
				const lineHeight = 21; // 14px font * 1.5 height
				const charWidth = 8.4; // Average 14px monospace character width
				
				const targetY = (pos.line * lineHeight) + 10; // Adding 10px top-padding
				const targetX = (pos.ch * charWidth) + 10; // 10px left-padding
				
				// 1. If the textarea is constrained and scrolls internally:
				if (textarea.scrollHeight > textarea.clientHeight + 20) {
					textarea.scrollTop = Math.max(0, targetY - (textarea.clientHeight / 2));
					textarea.scrollLeft = Math.max(0, targetX - (textarea.clientWidth / 2));
				}

				// 2. If the textarea has grown infinitely and pushed the scrollbar to the Window (e.g. no height constraint):
				const rect = textarea.getBoundingClientRect();
				const absoluteY = window.scrollY + rect.top + targetY;
				const absoluteX = window.scrollX + rect.left + targetX;

				// Scroll the main window to center the matched line
				window.scrollTo({
					top: Math.max(0, absoluteY - (window.innerHeight / 2)),
					left: Math.max(0, absoluteX - (window.innerWidth / 2)),
					behavior: 'auto'
				});
			},
			replaceRange: (text, start, end) => {
				const val = textarea.value;
				const new_text = val.substring(0, start.index) + text + val.substring(end.index);
				textarea.value = new_text;
				textarea.textContent = new_text;
				update_line_numbers();
			}
		};

		// Assign actual payload! (this acts as the bridge for this.editor.setValue called during init)
		textarea.value = content_display;

		// Initialize state
		update_line_numbers();

		// Apply security read-only state if instructed
		if (this.is_read_only || data.is_truncated) {
			this.editor.setOption('readOnly', true);
		}

		// Ensure fallback mock gets a working find panel
		if (!this.find_panel) {
			this.setup_find_replace();
		}

		this.show_status(data.is_truncated 
			? "⚠️ Offline mode - Preview truncated at 16KB" 
			: "ℹ️ Offline mode - Native editor active", "warning");
			
		textarea.focus();
	}

	async save_file() {
		if (this.is_read_only || !this.is_modified) {
			if (!this.is_modified) {
				this.show_status("No changes to save", "info");
			}
			return;
		}

		// Get password from input or cache (can be blank)
		const password = this.password_cached || (this.password_input ? this.password_input.value : "");

		this.save_btn.disabled = true;
		this.show_status("Saving...", "info");

		try {
			const content = this.editor ? this.editor.getValue() : "";
			
			// Use FormData to send file (like upload mechanism)
			const formData = new FormData();
			formData.append('post-type', 'save-code');
			formData.append('password', password);
			formData.append('content', content);
			formData.append('mod_time', this.current_mod_time || '0');
			formData.append('line_ending', this.line_ending_select ? this.line_ending_select.value : this.current_line_ending);

			const url = tools.add_query_here("save-file");
			const response = await fetch(url, {
				method: 'POST',
				body: formData
			});

			// Check if still active after async call
			if (!this.is_active) return;

			const data = await response.json();

			// Check if still active after async call
			if (!this.is_active) return;

			if (response.status === 409) {
				// Conflict: file was modified externally
				this.show_status("File was modified externally. Reload to see changes?", "warning");
				return;
			}

			if (!response.ok) {
				this.show_status(data.message || "Failed to save file", "error");
				return;
			}

			if (data.status === "success") {
				this.is_modified = false;
				this.current_mod_time = data.mod_time;
				this.update_unsaved_indicator();
				this.password_cached = password; // Cache password for next save on this page
				this.show_status("File saved successfully", "success");
			} else {
				this.show_status(data.message || "Save failed", "error");
			}

		} catch (error) {
			if (!this.is_active) return;
			console.error("Error saving file:", error);
			this.show_status("Error saving file: " + error.message, "error");
		} finally {
			this.save_btn.disabled = false;
		}
	}

	download_file() {
		if (!this.current_file_path) {
			this.show_status("No file loaded", "error");
			return;
		}

		try {
			const content = this.editor ? this.editor.getValue() : "";
			const file_name = this.file_title.innerText || "download.txt";
			
			// Create blob and download
			const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
			const link = document.createElement('a');
			const url = URL.createObjectURL(blob);
			
			link.href = url;
			link.download = file_name;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			URL.revokeObjectURL(url);
			
			this.show_status(`Downloaded: ${file_name}`, "success");
		} catch (error) {
			console.error("Error downloading file:", error);
			this.show_status("Download failed: " + error.message, "error");
		}
	}

	toggle_readonly() {
		// Don't allow toggling if file is truncated
		if (this.is_truncated) {
			this.show_status("Cannot enable edit mode for truncated files (too large)", "warning");
			return;
		}

		// Toggle read-only mode
		this.is_read_only = !this.is_read_only;
		if (this.editor) this.editor.setOption("readOnly", this.is_read_only);
		
		// Update button appearance
		this.save_btn.disabled = this.is_read_only;
			this.show_status(this.is_read_only ? "Editing disabled (Read-only mode)" : "Editing enabled", "info");
			this.update_readonly_button_state();
	}

	update_readonly_button_state() {
		this.readonly_toggle_btn.classList.toggle("readonly", this.is_read_only);
		
		if (this.is_read_only) {
			this.readonly_toggle_btn.innerHTML = '<span class="fa fa-regular fa-pen">🔓</span> <span class="btn-text">Enable Editing</span>';
			this.readonly_toggle_btn.title = "Enable Editing";
		} else {
			this.readonly_toggle_btn.innerHTML = '<span class="fa fa-regular fa-pen-slash">🔒</span> <span class="btn-text">Disable Editing</span>';
			this.readonly_toggle_btn.title = "Disable Editing";
		}
		
		theme_controller.del_fa_alt(this.readonly_toggle_btn);
	}

	update_unsaved_indicator() {
		this.unsaved_indicator.style.display = this.is_modified ? 'inline' : 'none';
		this.save_btn.disabled = !this.is_modified || this.is_read_only;
	}

	show_status(message, type = "info") {
		let bgcolor = '#005165ed';
		if (type === 'error') {
			bgcolor = '#f44336';
		} else if (type === 'warning') {
			bgcolor = '#ff9800';
		} else if (type === 'success') {
			bgcolor = '#4CAF50';
		} else if (type === 'info') {
			bgcolor = '#2196F3';
		}
		if (this.is_active) {
			toaster.toast(message, 3000, bgcolor);
		}
	}

	format_file_size(bytes) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
		// Recalculate CodeMirror dimensions if it was initialized while hidden
		if (this.editor) {
			setTimeout(() => {
				if (this.editor) this.editor.refresh();
			}, 50);
		}
	}

	destroy() {
		// Mark handler as inactive to prevent updating destroyed UI
		this.is_active = false;

		// Clear any pending timeouts
		this.pending_timeouts.forEach(timeoutId => clearTimeout(timeoutId));
		this.pending_timeouts = [];

		// Remove window beforeunload listener
		window.removeEventListener('beforeunload', this.beforeunload_listener);

		// Remove save button listener
		this.save_btn.removeEventListener('click', this.save_listener);

		// Remove CodeMirror change listener (only applies to real CodeMirror; offline mock lacks this)
		if (!this.is_fallback && this.editor) {
			this.editor.off('change', this.change_listener);
			// Destroy CodeMirror instance (cleanup DOM and internal state)
			this.editor.toTextArea();
		}
		this.editor = null;

		// Remove find/replace panel listeners
		this.find_panel_listeners.forEach(listener => {
			listener.element.removeEventListener(listener.type, listener.handler);
		});
		this.find_panel_listeners = [];

		// Remove find/replace panel from DOM
		this.find_panel.remove();
		this.find_panel = null;
	}

	clear() {
		if (this.editor) this.editor.setValue("");
		this.is_modified = false;
		this.current_file_path = null;
		this.current_mod_time = null;
		this.file_title.innerText = "";
		this.file_info.innerHTML = "";
		this.editor_status.innerText = "";
		
		// Reset button states
		this.save_btn.disabled = true;
		this.download_btn.disabled = true;
		this.readonly_toggle_btn.disabled = false;
			this.is_read_only = false;
			this.update_readonly_button_state();
	}
}

// Register the code editor page handler
page_controller.add_handler("code", CodeEditor_Page, "code-editor-page");