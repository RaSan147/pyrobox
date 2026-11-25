var r_li = []; // ${PY_LINK_LIST};
var f_li = []; // ${PY_FILE_LIST};
var s_li = []; // ${PY_FILE_SIZE};
var rs_li = []; // raw size
var mt_li = []; // mtimes


class UploadManager {
	constructor() {
		this.last_index = 1;
		this.uploaders = new Map();
		this.requests = new Map();
		this.status = new Map();
		/* Data Structure
		{index: form_element, ...}
		*/
		
		this.drag_pop_open = false;

		this.initDragDropHandlers();
	}

	initDragDropHandlers() {
		const file_list = byId("content_container");
		
		file_list.ondragover = async (event) => {
			event.preventDefault();
			
			// Check if files are being dragged (not links or other content)
			const hasFiles = Array.from(event.dataTransfer.items || []).some(item => item.kind === 'file');
			
			if (!hasFiles || this.drag_pop_open) return;
			
			this.drag_pop_open = true;
			const form = await this.new();
			
			popup_msg.createPopup("Upload Files", form, true, () => {
				this.drag_pop_open = false;
			});
			popup_msg.open_popup();
		};

		file_list.ondragleave = (event) => {
			event.preventDefault();
		};

		file_list.ondrop = (event) => {
			event.preventDefault();
		};
	}

	async new() {
		const index = this.last_index++;
		const form = this.createFormElement(index);
		this.selected_files = new DataTransfer();
		
		this.setupFormHandlers(form, index);
		return form;
	}

	createFormElement(index) {
		const form = createElement("form");
		form.id = `uploader-${index}`;
		form.className = "jsonly";
		form.method = "post";
		form.action = tools.full_path("?upload");
		form.enctype = "multipart/form-data";

		const center = createElement("center");
		center.appendChild(this.createHiddenInput("post-type", "upload"));
		center.appendChild(this.createPasswordInput());
		
		const up_files = createElement("input");
		up_files.type = "file";
		up_files.name = "file";
		up_files.multiple = true;
		up_files.hidden = true;
		center.appendChild(up_files);
		
		// center.appendChild(createElement("br"));
		// center.appendChild(createElement("br"));
		center.appendChild(this.createDragDropArea(up_files));
		
		form.appendChild(center);
		form.appendChild(this.createFileListContainer());
		form.appendChild(this.createSubmitSection());
		
		return form;
	}

	createHiddenInput(name, value) {
		const input = createElement("input");
		input.type = "hidden";
		input.name = name;
		input.value = value;
		return input;
	}

	createPasswordInput() {
		const container = createElement("div");
		container.className = "upload-pass-container";

		// If user is a logged-in member, password is not required
		if (typeof user !== 'undefined' && user.permissions && user.permissions.MEMBER) {
			container.style.display = "none";
		}
		
		const label = createElement("span");
		label.className = "upload-pass-label";
		const lockIcon = this.createIconElement("🔐", "", "fa fa-solid fa-lock");
		lockIcon.style.marginRight = "8px";
		label.appendChild(lockIcon);
		label.appendChild(document.createTextNode("Password:"));
		container.appendChild(label);
		
		const wrapper = createElement("div");
		wrapper.className = "upload-pass-wrapper";
		
		const input = createElement("input");
		input.type = "password";
		input.name = "password";
		input.placeholder = "Optional";
		input.className = "upload-pass-box";

		// Remember session / -k password for guest in sessionStorage
		if (typeof pref_store !== 'undefined') {
			const savedPass = pref_store.get('upload_pass', '', true);
			if (savedPass) {
				input.value = savedPass;
			}
			input.addEventListener('change', () => {
				if (input.value) {
					pref_store.set('upload_pass', input.value, true);
				}
			});
		}

		wrapper.appendChild(input);
		
		const eyeBtn = createElement("button");
		eyeBtn.type = "button";
		eyeBtn.className = "upload-pass-eye";
		const eyeIcon = this.createIconElement("👁", "", "fa fa-solid fa-eye");
		eyeBtn.appendChild(eyeIcon);
		
		eyeBtn.onclick = (e) => {
			e.preventDefault();
			const isPass = input.type === "password";
			input.type = isPass ? "text" : "password";
			eyeBtn.innerHTML = "";
			const newIcon = this.createIconElement(isPass ? "𓂀" : "👁", "", isPass ? "fa fa-solid fa-eye-slash" : "fa fa-solid fa-eye");
			eyeBtn.appendChild(newIcon);
		};
		
		wrapper.appendChild(eyeBtn);
		container.appendChild(wrapper);
		
		return container;
	}

	createDragDropArea(fileInput) {
		const uploader_box = createElement("div");
		uploader_box.className = "upload-box-outer";
		
		const dragArea = createElement("div");
		dragArea.className = "drag-area";
		dragArea.id = "drag-area";
		dragArea.onclick = () => fileInput.click();
		
		const iconContainer = createElement("div");
		iconContainer.className = "drag-icon-wrapper";
		iconContainer.appendChild(this.createIconElement("☁️", "drag-icon", "fa fa-solid fa-cloud-arrow-up"));
		dragArea.appendChild(iconContainer);
		
		const header = createElement("header");
		header.innerText = "Click or Drag Files here";
		dragArea.appendChild(header);
		
		const subtitle = createElement("p");
		subtitle.innerText = "Upload directories and multiple files";
		dragArea.appendChild(subtitle);
		
		// Unified file/folder selection button
		const buttonContainer = createElement("div");
		buttonContainer.className = "upload-button-container";
		
		const browseButton = this.createBrowseButton();
		buttonContainer.appendChild(browseButton);
		dragArea.appendChild(buttonContainer);
		
		// Hidden folder input that we'll use when needed
		const folderInput = createElement("input");
		folderInput.type = "file";
		folderInput.name = "folder";
		folderInput.webkitdirectory = true;
		folderInput.multiple = true;
		folderInput.hidden = true;
		dragArea.appendChild(folderInput);
		
		// Dynamic input handler
		fileInput.addEventListener('change', (e) => {
			if (e.target.files.length > 0) {
				// console.log("Files selected", e.target.files);
				this.addFiles(e.target.files, fileInput);
			}
		});
		
		folderInput.addEventListener('change', async (e) => {
			if (e.target.files.length > 0) {
				// console.log("Folder selected", e.target.files);
				const files = await this.processFolderContents(e.target.files);
				this.addFiles(files, folderInput); // Fixed to use folderInput
			}
		});
		
		// Smart click handler that detects folder upload requests
		browseButton.onclick = (e) => {
			e.stopPropagation();
			if (e.shiftKey || e.ctrlKey || e.metaKey) {
				// Modified click = folder upload
				folderInput.click();
			} else {
				// Regular click = file upload
				fileInput.click();
			}
		};
		
		this.setupDragDropHandlers(dragArea, fileInput, header);
		uploader_box.appendChild(dragArea);
		
		return uploader_box;
	}

	createIconElement(iconText, className, faClass) {
		const element = createElement("span");
		element.className = (className ? className + " " : "") + (faClass ? `fa ${faClass}` : "");
		element.innerText = iconText;
		
		if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
			theme_controller.del_fa_alt(element);
		}
		return element;
	}

	createBrowseButton() {
		const button = createElement("button");
		button.type = "button";
		button.className = "drag-browse";
		
		const icon = this.createIconElement("📁", "", "fa fa-solid fa-folder-open");
		icon.style.marginRight = "8px";
		button.appendChild(icon);
		
		const text = createElement("span");
		text.innerText = "Select Files";
		button.appendChild(text);

		return button;
	}

	setupDragDropHandlers(dragArea, fileInput, header) {
		dragArea.ondragover = (event) => {
			event.preventDefault();
			event.stopPropagation();
			
			// Check if any files are being dragged (not just links or other types)
			const hasFiles = Array.from(event.dataTransfer.items || []).some(item => item.kind === 'file');
			
			if (hasFiles) {
				dragArea.classList.add("active");
				header.innerText = "Drop to add files";
				event.dataTransfer.dropEffect = "copy";
			} else {
				dragArea.classList.remove("active");
				event.dataTransfer.dropEffect = "none";
			}
		};

		dragArea.ondragleave = (event) => {
			event.preventDefault();
			event.stopPropagation();
			dragArea.classList.remove("active");
			header.innerText = "Click or Drag Files here";
		};

		dragArea.ondrop = async (event) => {
			event.preventDefault();
			event.stopPropagation();
			dragArea.classList.remove("active");
			header.innerText = "Click or Drag Files here";

			const items = event.dataTransfer.items;
			const files = [];
			
			// Process all items (files and folders)
			const processItem = async (item) => {
				if (item.kind === 'file') {
					const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
					if (entry) {
						if (entry.isFile) {
							const file = item.getAsFile();
							files.push(file);
						} else if (entry.isDirectory) {
							const folderFiles = await this.processDirectoryEntry(entry);
							files.push(...folderFiles);
						}
					} else {
						// Fallback for browsers without webkitGetAsEntry
						const file = item.getAsFile();
						if (file) files.push(file);
					}
				}
			};

			await Promise.all([...items].map(processItem));
			
			if (files.length > 0) {
				// console.log("Files dropped", files);
				this.addFiles(files, fileInput);
			}
		};
	}

	async processDirectoryEntry(directoryEntry) {
		const files = [];
		const directoryPath = (directoryEntry.fullPath || directoryEntry.name).replace(/^\/+/, '');
	
		const readEntries = (reader) => {
			return new Promise((resolve) => {
				reader.readEntries(async (entries) => {
					if (!entries || entries.length === 0) {
						return resolve([]);
					}
	
					for (const entry of entries) {
						if (entry.isFile) {
							const file = await this.getFileFromEntry(entry);
							if (file) {
								// Store the full relative path including the directory name
								file._relativePath = directoryPath + '/' + entry.name;
								files.push(file);
							}
						} else if (entry.isDirectory) {
							const folderFiles = await this.processDirectoryEntry(entry);
							files.push(...folderFiles);
						}
					}
					resolve(entries);
				}, () => resolve([])); // Handle readEntries failure
			});
		};
	
		const reader = directoryEntry.createReader();
		let entries;
		do {
			entries = await readEntries(reader);
		} while (entries.length > 0);
	
		return files;
	}

	getFileFromEntry(fileEntry) {
		return new Promise((resolve) => {
			fileEntry.file((file) => {
				resolve(file);
			});
		});
	}

	async processFolderContents(files) {
		const processedFiles = [];
		
		for (let i = 0; i < files.length; i++) {
			const file = files[i];
			// For folder uploads, webkitRelativePath contains the full path
			if (file.webkitRelativePath) {
				file._relativePath = file.webkitRelativePath;
			}
			processedFiles.push(file);
		}
		
		return processedFiles;
	}

	createFileListContainer() {
		const container = createElement("div");
		container.style.display = "none";
		
		const title = createElement("h2");
		title.innerText = "Selected Files";
		title.className = "has-selected-files";
		title.style.textAlign = "center";
		container.appendChild(title);
		
		const fileDisplay = createElement("div");
		fileDisplay.className = "drag-file-list";
		container.appendChild(fileDisplay);
		
		return container;
	}

	createSubmitSection() {
		const fragment = document.createDocumentFragment();
		
		const center = createElement("center");
		const submitButton = createElement("button");
		submitButton.type = "submit";
		submitButton.className = "drag-browse upload-button";
		
		const icon = this.createIconElement("🚀", "", "fa fa-solid fa-rocket");
		icon.style.marginRight = "10px";
		submitButton.appendChild(icon);
		
		const text = createElement("span");
		text.innerText = "Start Upload";
		submitButton.appendChild(text);
		
		center.appendChild(submitButton);
		
		const statusLabel = createElement("span");
		statusLabel.innerText = "Status: ";
		
		const statusText = createElement("span");
		statusText.className = "upload-pop-status";
		statusText.innerText = "Waiting";
		statusLabel.appendChild(statusText);
		statusLabel.style.display = "none";
		statusLabel.style.marginTop = "10px";
		center.appendChild(statusLabel);
		
		fragment.appendChild(center);
		return fragment;
	}

	setupFormHandlers(form, index) {
		let that = this;

		let fileInput = form.querySelector('input[type="file"]');
		let submitButton = form.querySelector('button[type="submit"]');
		this.fileDisplay = form.querySelector('.drag-file-list');
		this.fileContainer = form.querySelector('div:has(.drag-file-list)');
		let statusLabel = form.querySelector('span:has(.upload-pop-status)');
		let statusText = statusLabel.querySelector('.upload-pop-status');

		form.onsubmit = (e) => {
			e.preventDefault();

			// remove the folder input from the form data
			if (form.querySelector('input[name="folder"]')) {
				form.querySelector('input[name="folder"]').remove();
			}
			
			// Create a new FormData and append all files with their relative paths
			const formData = new FormData();
			
			// Copy all form fields except files
			for (const pair of new FormData(e.target)) {
				if (pair[0] !== 'file') {
					formData.append(pair[0], pair[1]);
				}
				if (pair[0] === 'password' && pair[1] && typeof pref_store !== 'undefined') {
					pref_store.set('upload_pass', pair[1], true);
				}
			}
			
			// Append all files with their relative paths
			for (let i = 0; i < this.selected_files.files.length; i++) {
				const file = this.selected_files.files[i];
				const path = (file._relativePath || file.name).replace(/^\/+/, '');
				formData.append('file[]', file, path);
			}
			
			that.handleFormSubmit(e, index, submitButton, statusText, statusLabel, formData);
		};
	}

	addFiles(files, fileInput) {
		this.removeDuplicates(files);
		fileInput.files = this.selected_files.files;
		this.showFiles();
	}

	removeDuplicates(files) {
		const getPath = f => f._relativePath || f.name;
		let existingPaths = new Set([...this.selected_files.files].map(getPath));

		for (let file of files) {
			let path = getPath(file);
			if (existingPaths.has(path)) {
				toaster.toast(this.truncateFileName(path) + " already selected", 1500);
				continue;
			}
			this.selected_files.items.add(file);
			existingPaths.add(path);
		}
	}

	truncateFileName(name) {
		return name.length > 20 ? `${name.slice(0, 7)}...${name.slice(-6)}` : name;
	}

	showFiles() {
		let selected_files = this.selected_files;
		let fileContainer = this.fileContainer;
		let fileDisplay = this.fileDisplay;

		tools.del_child(fileDisplay);

		if (selected_files.files.length) {
			fileContainer.style.display = "contents";
			let fragment = document.createDocumentFragment();
			
			for (let i = 0; i < selected_files.files.length; i++) {
				fragment.appendChild(this.createFileItem(selected_files.files[i], i, selected_files, fileDisplay, fileContainer));
			}
			
			fileDisplay.appendChild(fragment);
		} else {
			fileContainer.style.display = "none";
		}
	}

	createFileItem(file, index, selected_files, fileDisplay, fileContainer) {
		selected_files = selected_files || this.selected_files;

		let item = createElement("div");
		item.className = "upload-file-item";
		
		let folderIconClass = file._relativePath && file._relativePath.includes('/') ? "fa fa-solid fa-folder" : "fa fa-solid fa-file";
		let icon = this.createIconElement(file._relativePath && file._relativePath.includes('/') ? "📁" : "📄", "", folderIconClass);
		icon.style.marginRight = "12px";
		icon.style.fontSize = "18px";
		item.appendChild(icon);

		let nameCell = createElement("div");
		nameCell.className = "ufname";
		// Show the relative path if available
		nameCell.innerText = file._relativePath || file.name;
		item.appendChild(nameCell);
		
		let sizeCell = createElement("div");
		sizeCell.className = "ufsize";
		sizeCell.innerText = fmbytes(file.size);
		item.appendChild(sizeCell);
		
		let removeCell = createElement("button");
		removeCell.type = "button";
		removeCell.className = "ufdel";
		let delIcon = this.createIconElement("×", "", "fa fa-solid fa-xmark");
		removeCell.appendChild(delIcon);
		removeCell.onclick = (e) => {
			e.stopPropagation();
			this.removeFileFromList(index, fileDisplay);
		};
		item.appendChild(removeCell);
		
		return item;
	}

	removeFileFromList(index, fileDisplay) {
		let selected_files = this.selected_files;

		let dt = new DataTransfer();
		
		for (let i = 0; i < selected_files.files.length; i++) {
			if (index !== i) dt.items.add(selected_files.files[i]);
		}
		
		selected_files = dt;
		this.selected_files = selected_files;
		this.showFiles(fileDisplay);
	}

	handleFormSubmit(e, index, submitButton, statusText, statusLabel, formData) {
		if (this.status.get(index)) {
			this.cancel(index);
			this.showStatus("Upload cancelled", statusText, statusLabel);
			return;
		}
		
		if (!this.selected_files.files.length) {
			toaster.toast("No files selected");
			return;
		}
		
		this.status.set(index, true);
		const request = new XMLHttpRequest();
		this.requests.set(index, request);
		this.uploaders.set(index, e.target);
		submitButton.innerHTML = "";
		const icon = this.createIconElement("⏹️", "", "fa fa-solid fa-stop");
		icon.style.marginRight = "8px";
		submitButton.appendChild(icon);
		const text = createElement("span");
		text.innerText = "Cancel";
		submitButton.appendChild(text);
		
		popup_msg.close();
		
		var prog_id = `upload-${index}`;
		
		if (!progress_bars.bar_elements[prog_id]) {
			prog_id = progress_bars.new(
				'upload', 
				prog_id, 
				window.location.href,
				{
					"onclick": () => {
						this.show(index);
					},
					"oncancel": () => {
						this.cancel(index);
					}
				}
			);
			e.target.prog_id = prog_id;
		}
			
		
		this.setupRequestHandlers(request, e, prog_id, index, submitButton, statusText, statusLabel);
		request.send(formData);
	}

	setupRequestHandlers(request, e, prog_id, index, submitButton, statusText, statusLabel) {
		request.open(e.target.method, e.target.action);
		request.setRequestHeader('Cache-Control', 'no-cache');
		// request.setRequestHeader("Connection", "close");
		
		request.onreadystatechange = () => {
			if (request.readyState !== XMLHttpRequest.DONE) return;
			
			let msg, color, status;
			if (request.status === 401) {
				msg = 'Incorrect password';
				color = "red";
				status = "error";
			} else if (request.status === 503) {
				msg = 'Upload is disabled';
				color = "red";
				status = "error";
			} else if (request.status === 0) {
				msg = 'Connection failed';
				color = "red";
				status = "error";
			} else if (request.status === 204 || request.status === 200) {
				msg = 'Success';
				color = "green";
				status = "done";
				page_controller.refresh_dir();
			} else {
				msg = `${request.status}: ${request.statusText}`;
				color = "red";
				status = "error";
			}
			
			this.handleUploadComplete(prog_id, index, submitButton, statusText, msg, color, status);
		};
		
		request.upload.onprogress = e => {
			const percent = Math.floor(100 * e.loaded / e.total);
			const msg = e.loaded === e.total ? 'Saving...' : `Progress ${percent}%`;
			
			this.showStatus(msg, statusText, statusLabel);
			progress_bars.update(prog_id, {
				"status_text": msg,
				"status_color": "green",
				"status": "running",
				"percent": percent
			});
		};
	}

	handleUploadComplete(prog_id, index, submitButton, statusText, msg, color, status) {
		progress_bars.update(prog_id, {
			"status_text": msg,
			"status_color": color,
			"status": status,
			"percent": status === "done" ? 100 : 0
		});
		
		submitButton.innerText = "➾ Re-upload";
		if (!this.status.get(index)) return;
		
		this.showStatus(msg, statusText);
		this.status.set(index, false);
		
		const toastMsg = status === "error" ? "Upload Failed" : "Upload Complete";
		toaster.toast(toastMsg, 3000, color);
	}

	showStatus(msg, statusText, statusLabel) {
		if (statusLabel) statusLabel.style.display = "block";
		if (statusText) statusText.innerText = msg;
	}

	show(index) {
		let form = this.uploaders.get(index);
		if (!form) {
			toaster.toast("No form found");
			return;
		}
		popup_msg.createPopup("Upload Files", form);
		popup_msg.show();
	}

	cancel(index, remove = false) {
		const request = this.requests.get(index);
		const form = this.uploaders.get(index);
		
		if (form) {
			form.querySelector(".upload-button").innerText = "➾ Upload";
		}
		
		progress_bars.update(form?.prog_id, {
			"status_text": "Upload Canceled",
			"status_color": "red",
			"status": "error",
			"percent": 0
		});
		
		if (this.status.get(index)) {
			this.status.set(index, false);
			request?.abort();
			if (!remove) toaster.toast("Upload Canceled");
			return true;
		}
		return false;
	}

	remove(index) {
		this.cancel(index, true);
		const form = this.uploaders.get(index);
		progress_bars.remove(form?.prog_id);
		form?.remove();
		this.uploaders.delete(index);
		this.requests.delete(index);
	}
}

const upload_man = new UploadManager();

class FileManager {
	constructor() {
		this.typeIcons = {
			'd': { icon: '📁', faClass: 'fa-solid fa-folder', class: 'link folder', type: 'folder' },
			'v': { icon: '🎬', faClass: 'fa-solid fa-film', class: 'vid video', type: 'video' },
			'a': { icon: '🎵', faClass: 'fa-solid fa-music', class: 'vid audio', type: 'audio' },
			'i': { icon: '🖼️', faClass: 'fa-solid fa-image', class: 'file image', type: 'image' },
			'f': { icon: '📄', faClass: 'fa-solid fa-file-lines', class: 'file', type: 'file' },
			'h': { icon: '🔗', faClass: 'fa-solid fa-link', class: 'html', type: 'html' }
		};
	}

	show_more_menu() {
		const menu = createElement("div");
		
		const options = [
			{
				text: "Sort By",
				emoji: "🔀",
				faClass: "fa-solid fa-arrow-down-wide-short",
				className: "disable_selection popup-btn menu_options",
				action: () => this.Show_sort_by()
			},
			{
				text: "New Folder", 
				emoji: "📁",
				faClass: "fa-solid fa-folder-plus",
				className: "disable_selection popup-btn menu_options",
				action: () => this.Show_folder_maker()
			},
			{ 
				text: "Upload Files", 
				emoji: "📤",
				faClass: "fa-solid fa-cloud-arrow-up",
				className: `disable_selection popup-btn menu_options ${user.permissions.NOPERMISSION || !user.permissions.UPLOAD ? "disabled" : ""}`,
				action: () => this.Show_upload_files()
			}
		];
		
		options.forEach(opt => {
			if (opt.className.includes("disabled")) return;
			
			const element = createElement("div");
			element.className = opt.className;

			const iconSpan = createElement("span");
			iconSpan.className = "menu-icon fa " + opt.faClass;
			iconSpan.innerText = opt.emoji;

			const labelSpan = createElement("span");
			labelSpan.className = "menu-label";
			labelSpan.innerText = opt.text;

			element.appendChild(iconSpan);
			element.appendChild(labelSpan);

			if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
				theme_controller.del_fa_alt(iconSpan);
			}

			element.onclick = opt.action;
			menu.appendChild(element);
		});
		
		popup_msg.createPopup("Options", menu);
		popup_msg.open_popup();
	}

	Show_folder_maker() {
		popup_msg.createPopup(
			"Create Folder",
			`<div class="popup-form">
				<label class="popup-form-label">Enter folder name:</label>
				<input id="folder-name" class="popup-input" type="text" placeholder="New folder name" autocomplete="off">
				<div class="popup-actions-row">
					<button type="button" class="btn btn-primary" onclick="context_menu.create_folder()">Create</button>
					<button type="button" class="btn" onclick="popup_msg.close()">Cancel</button>
				</div>
			</div>`
		);
		popup_msg.open_popup();
		const input = byId("folder-name");
		if (input) {
			input.focus();
			input.onkeydown = (e) => {
				if (e.key === "Enter") {
					context_menu.create_folder();
				}
			};
		}
	}

	Show_sort_by() {
		const menu = createElement("div");

		const options = [
			{ text: "Name (Asc)", action: () => this.sort_files("name", "asc") },
			{ text: "Name (Desc)", action: () => this.sort_files("name", "desc") },
			{ text: "Size (Asc)", action: () => this.sort_files("size", "asc") },
			{ text: "Size (Desc)", action: () => this.sort_files("size", "desc") },
			{ text: "Date Modified (Asc)", action: () => this.sort_files("date", "asc") },
			{ text: "Date Modified (Desc)", action: () => this.sort_files("date", "desc") },
		];

		options.forEach(opt => {
			const element = createElement("div");
			element.innerText = opt.text;
			element.className = "disable_selection popup-btn menu_options";
			element.onclick = () => {
				popup_msg.close();
				opt.action();
			};
			menu.appendChild(element);
		});

		popup_msg.createPopup("Sort By", menu);
		popup_msg.open_popup();
	}

	sort_files(type, order) {
		// Note: Name sorting depends on python given sorting (natural sort)
		if (!this.orig_order) {
			this.orig_order = r_li.map((_, i) => i);
		}

		pref_store.set("sort_type", type);
		pref_store.set("sort_order", order);

		let zipped = r_li.map((r, i) => ({
			r: r, f: f_li[i], s: s_li[i], rs: rs_li[i], mt: mt_li[i], orig: this.orig_order[i]
		}));
		
		zipped.sort((a, b) => {
			let valA, valB;
			if (type === "name") {
				valA = a.orig; valB = b.orig;
			} else if (type === "size") {
				valA = a.rs; valB = b.rs;
			} else if (type === "date") {
				valA = a.mt; valB = b.mt;
			}

			if (valA < valB) return order === "asc" ? -1 : 1;
			if (valA > valB) return order === "asc" ? 1 : -1;
			return 0;
		});

		r_li = zipped.map(z => z.r);
		f_li = zipped.map(z => z.f);
		s_li = zipped.map(z => z.s);
		rs_li = zipped.map(z => z.rs);
		mt_li = zipped.map(z => z.mt);
		this.orig_order = zipped.map(z => z.orig);

		this.show_file_list();
	}

	async Show_upload_files() {
		const form = await upload_man.new();
		popup_msg.createPopup("Upload Files", form);
		popup_msg.open_popup();
	}

	show_file_list() {
		const dir_container = byId("js-content_list");
		const fragment = document.createDocumentFragment();
		
		const { folderFragment, fileFragment } = this.createFileFragments();
		
		if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
			theme_controller.del_fa_alt(folderFragment);
			theme_controller.del_fa_alt(fileFragment);
		}

		fragment.appendChild(folderFragment);
		fragment.appendChild(fileFragment);
		
		this.clear_file_list();
		dir_container.appendChild(fragment);
	}

	createFileFragments() {
		const folderFragment = createElement('div');
		const fileFragment = createElement('div');
		
		r_li.forEach((r, i) => {
			const typeInfo = this.typeIcons[r[0]];
			if (!typeInfo) return;
			
			const item = this.createFileItem(r, i, typeInfo);
			
			if (r.startsWith('d')) {
				folderFragment.appendChild(item);
			} else {
				fileFragment.appendChild(item);
			}
		});
		
		return { folderFragment, fileFragment };
	}

	createFileItem(r, i, typeInfo) {
		const r_ = r.slice(1);
		const name = f_li[i];
		
		const item = createElement('div');
		item.classList.add("dir_item");
		
		const link = createElement('a');
		
		// Determine link action based on file type
		const text_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.htm', '.css', '.scss', '.less', 
								  '.json', '.xml', '.md', '.txt', '.sql', '.java', '.cpp', '.c', '.h', '.go', 
								  '.rs', '.php', '.rb', '.yaml', '.yml', '.sh', '.bash', '.conf', '.cfg', '.ini', 
								  '.properties', '.gradle', '.maven'];
		const file_ext = name.substr(name.lastIndexOf('.')).toLowerCase();
		
		let itemTypeInfo = typeInfo;

		if (r.startsWith('v') || r.startsWith('a')) {
			// Video or Audio media files
			link.href = go_link("vid", r_);
		} else if (text_extensions.includes(file_ext)) {
			// Text files - open in editor
			link.href = go_link("edit", r_);
			itemTypeInfo = { icon: '📝', faClass: 'fa-solid fa-file-code', class: 'file code', type: 'file' };
		} else {
			// Other files - normal download link
			link.href = r_;
		}
		
		link.title = name;
		link.className = `all_link disable_selection ${itemTypeInfo.class}`;
		
		link.appendChild(this.createIconElement(itemTypeInfo.icon, itemTypeInfo.faClass));
		link.appendChild(this.createNameElement(name, s_li[i]));
		
		link.oncontextmenu = (ev) => {
			ev.preventDefault();
			context_menu.show_menus(r_, name, itemTypeInfo.type);
			return false;
		};
		
		item.appendChild(link);
		item.appendChild(createElement("hr"));

		if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
			theme_controller.del_fa_alt(item);
		}
		
		return item;
	}

	createIconElement(icon, faClass) {
		const element = createElement("span");
		element.className = "link_icon" + (faClass ? ` fa ${faClass}` : "");
		element.innerText = icon;
		return element;
	}

	createNameElement(name, size) {
		const container = createElement("div");
		container.className = "link_text_container";
		
		const nameElement = createElement("span");
		nameElement.className = "link_name";
		nameElement.innerText = name;
		container.appendChild(nameElement);
		
		if (size) {
			const sizeElement = createElement("span");
			sizeElement.className = "link_size";
			sizeElement.innerText = size;
			container.appendChild(sizeElement);
		}
		
		return container;
	}

	clear_file_list() {
		tools.del_child("linkss");
		tools.del_child("js-content_list");
	}
}

const fm = new FileManager();




class FM_Page extends Page {
	constructor(controller=page_controller, type="dir", my_part="fm_page") {
		super(controller, type, my_part);
	}

	async initialize(lazyload = false) {
		if (!lazyload) {
			this.controller.clear();
		}

		this.set_title("File Manager");
		this.controller.set_actions_button_text("Tools", { class: "fa-solid fa-wrench", text: "🛠" });
		
		this.controller.set_action_tools([
			{
				text: "Upload Files",
				icon_class: "fa-solid fa-file-arrow-up",
				icon_text: "⬆️",
				action: () => fm.Show_upload_files(),
				condition: () => !(user.permissions.NOPERMISSION || !user.permissions.UPLOAD)
			},
			{
				text: "New Folder",
				icon_class: "fa-solid fa-folder-plus",
				icon_text: "📁",
				action: () => fm.Show_folder_maker()
			},
			{
				text: "Sort By",
				icon_class: "fa-solid fa-sort",
				icon_text: "🔽",
				action: () => fm.Show_sort_by()
			}
		]);

		this.controller.show_actions_button();

		if (user.permissions.NOPERMISSION || !user.permissions.VIEW) {
			this.set_title("No Permission");

			const container = byId("js-content_list");
			const warning = createElement("h2");
			warning.innerText = "You don't have permission to view this page";
			container.appendChild(warning);

			return;
		}

		var folder_data = await fetch(tools.add_query_here("folder_data"))
			.then(response => response.json())
			.catch(error => {
				console.error('There has been a problem with your fetch operation:', error); // TODO: Show error in page
			});

		if (!folder_data || !folder_data["status"] || folder_data.status == "error") {
			console.error("Error getting folder data"); // TODO: Show error in page
			return;
		}

		r_li = folder_data.type_list;
		f_li = folder_data.file_list;
		s_li = folder_data.size_list;
		rs_li = folder_data.raw_size_list || Array(f_li.length).fill(0);
		mt_li = folder_data.mtime_list || Array(f_li.length).fill(0);

		var title = folder_data.title;

		this.set_title(title);

		// Reset original order for the new folder
		fm.orig_order = null;

		// Await FontAwesome ready before first render so icons are swapped in-memory without flash
		if (typeof theme_controller !== 'undefined' && theme_controller.fa_ready_promise && !theme_controller.fa_ok) {
			await Promise.race([
				theme_controller.fa_ready_promise,
				new Promise(r => setTimeout(r, 400))
			]);
		}

		let sort_type = pref_store.get("sort_type");
		let sort_order = pref_store.get("sort_order");

		if (sort_type && sort_order) {
			fm.sort_files(sort_type, sort_order);
		} else {
			fm.show_file_list();
		}
	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
		tools.del_child("linkss");
	}
}

page_controller.add_handler("dir", FM_Page, "fm_page");

