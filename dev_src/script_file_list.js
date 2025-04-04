var r_li = []; // ${PY_LINK_LIST};
var f_li = []; // ${PY_FILE_LIST};
var s_li = []; // ${PY_FILE_SIZE};

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
			if (this.drag_pop_open) return;
			
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
		
		center.appendChild(createElement("br"));
		center.appendChild(createElement("br"));
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
		const container = createElement("span");
		container.className = "upload-pass";
		
		const label = document.createTextNode("Password:  ");
		container.appendChild(label);
		
		const input = createElement("input");
		input.type = "password";
		input.name = "password";
		input.placeholder = "Password";
		input.className = "upload-pass-box";
		container.appendChild(input);
		
		return container;
	}

	createDragDropArea(fileInput) {
		const uploader_box = createElement("div");
		uploader_box.className = "upload-box";
		
		const dragArea = createElement("div");
		dragArea.className = "drag-area";
		dragArea.id = "drag-area";
		
		dragArea.appendChild(this.createIconElement("⬆️", "drag-icon"));
		
		const header = this.createHeaderElement("Drag & Drop Files or Folders");
		dragArea.appendChild(header);
		
		dragArea.appendChild(this.createTextElement("OR"));
		
		// Unified file/folder selection button
		const buttonContainer = createElement("div");
		buttonContainer.className = "upload-button-container";
		
		const browseButton = this.createBrowseButton(fileInput, "Browse Files/Folders");
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
				this.addFiles(files, fileInput);
			}
		});
		
		// Smart click handler that detects folder upload requests
		browseButton.onclick = (e) => {
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

	createIconElement(icon, className) {
		const element = createElement("div");
		element.className = className;
		element.innerText = icon;
		return element;
	}

	createHeaderElement(text) {
		const element = createElement("header");
		element.innerText = text;
		return element;
	}

	createTextElement(text) {
		const element = createElement("span");
		element.innerText = text;
		return element;
	}

	createBrowseButton(fileInput) {
		const button = createElement("button");
		button.type = "button";
		button.innerText = "Browse File";
		button.className = "drag-browse";
		button.onclick = () => fileInput.click();
		return button;
	}

	setupDragDropHandlers(dragArea, fileInput, header) {
		dragArea.ondragover = (event) => {
			event.preventDefault();
			dragArea.classList.add("active");
			header.innerText = "Release to Upload";
		};

		dragArea.ondragleave = () => {
			dragArea.classList.remove("active");
			header.innerText = "Drag & Drop Files or Folders";
		};

		dragArea.ondrop = async (event) => {
			event.preventDefault();
			dragArea.classList.remove("active");
			header.innerText = "Drag & Drop Files or Folders";

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
		const directoryPath = directoryEntry.fullPath || directoryEntry.name;
	
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
		
		fragment.appendChild(createElement("br"));
		
		const center = createElement("center");
		const submitButton = createElement("button");
		submitButton.type = "submit";
		submitButton.innerText = "➾ Upload";
		submitButton.className = "drag-browse upload-button";
		center.appendChild(submitButton);
		
		center.appendChild(createElement("br"));
		center.appendChild(createElement("br"));
		
		const statusLabel = createElement("span");
		statusLabel.innerText = "Status: ";
		
		const statusText = createElement("span");
		statusText.className = "upload-pop-status";
		statusText.innerText = "Waiting";
		statusLabel.appendChild(statusText);
		statusLabel.style.display = "none";
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
			}
			
			// Append all files with their relative paths
			for (let i = 0; i < this.selected_files.files.length; i++) {
				const file = this.selected_files.files[i];
				const path = file._relativePath || file.name;
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
		let fileNames = new Set([...this.selected_files.files].map(f => f.name));

		for (let file of files) {
			if (fileNames.has(file.name)) {
				toaster.toast(this.truncateFileName(file.name) + " already selected", 1500);
				continue;
			}
			this.selected_files.items.add(file);
			fileNames.add(file.name);
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

		let item = createElement("table");
		item.className = "upload-file-item";
		
		let nameCell = createElement("td");
		nameCell.className = "ufname";
		// Show the relative path if available
		nameCell.innerText = file._relativePath || file.name;
		item.appendChild(nameCell);
		
		let sizeCell = createElement("td");
		sizeCell.className = "ufsize";
		sizeCell.innerHTML = `<span>${fmbytes(file.size)}</span>`;
		item.appendChild(sizeCell);
		
		let removeCell = createElement("td");
		removeCell.className = "ufremove";
		removeCell.innerHTML = `<span>&times;</span>`;
		removeCell.onclick = () => this.removeFileFromList(index, fileDisplay);
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
		
		submitButton.innerText = "⏹️ Cancel";
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
			'd': { icon: '📂', class: 'link', type: 'folder' },
			'v': { icon: '🎥', class: 'vid', type: 'video' },
			'i': { icon: '🌉', class: 'file', type: 'image' },
			'f': { icon: '📄', class: 'file', type: 'file' },
			'h': { icon: '🔗', class: 'html', type: 'html' }
		};
	}

	show_more_menu() {
		const menu = createElement("div");
		
		const options = [
			{ 
				text: "Sort By", 
				className: "disable_selection popup-btn menu_options debug_only",
				action: () => this.Show_sort_by()
			},
			{ 
				text: "New Folder", 
				className: "disable_selection popup-btn menu_options",
				action: () => this.Show_folder_maker()
			},
			{ 
				text: "Upload Files", 
				className: `disable_selection popup-btn menu_options ${user.permissions.NOPERMISSION || !user.permissions.UPLOAD ? "disabled" : ""}`,
				action: () => this.Show_upload_files()
			}
		];
		
		options.forEach(opt => {
			if (opt.className.includes("disabled")) return;
			
			const element = createElement("div");
			element.innerText = opt.text;
			element.className = opt.className;
			element.onclick = opt.action;
			menu.appendChild(element);
		});
		
		popup_msg.createPopup("Options", menu);
		popup_msg.open_popup();
	}

	Show_folder_maker() {
		popup_msg.createPopup(
			"Create Folder",
			`Enter folder name: <input id='folder-name' type='text'><br><br>
			 <div class='pagination center' onclick='context_menu.create_folder()'>Create</div>`
		);
		popup_msg.open_popup();
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
		link.href = r.startsWith('v') ? go_link("vid", r_) : r_;
		link.title = name;
		link.className = `all_link disable_selection ${typeInfo.class}`;
		
		link.appendChild(this.createIconElement(typeInfo.icon));
		link.appendChild(this.createNameElement(name, s_li[i]));
		
		link.oncontextmenu = (ev) => {
			ev.preventDefault();
			context_menu.show_menus(r_, name, typeInfo.type);
			return false;
		};
		
		item.appendChild(link);
		item.appendChild(createElement("hr"));
		
		return item;
	}

	createIconElement(icon) {
		const element = createElement("span");
		element.className = "link_icon";
		element.innerHTML = icon.toHtmlEntities();
		return element;
	}

	createNameElement(name, size) {
		const element = createElement("span");
		element.className = "link_name";
		element.innerText = ` ${name}`;
		
		if (size) {
			element.appendChild(createElement("br"));
			
			const sizeElement = createElement("span");
			sizeElement.className = "link_size";
			sizeElement.innerText = size;
			element.appendChild(sizeElement);
		}
		
		return element;
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

	on_action_button() {
		// show add folder, sort, etc
		fm.show_more_menu();
	}

	async initialize(lazyload = false) {
		if (!lazyload) {
			this.controller.clear();
		}

		this.set_title("File Manager");
		this.controller.set_actions_button_text("New&nbsp;");
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

		var title = folder_data.title;

		this.set_title(title);


		fm.show_file_list();
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

