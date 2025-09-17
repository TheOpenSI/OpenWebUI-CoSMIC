<script lang="ts">
	import { toast } from "svelte-sonner";
	import { onMount, getContext, createEventDispatcher } from "svelte";

	const dispatch = createEventDispatcher();

	import { updateQuerySettings, resetVectorDB } from "$lib/apis/retrieval";

	import {
		getCoSMICConfig,
		updateCoSMICConfig,
		uploadChessFile,
	} from "$lib/apis/cosmic";

	import { deleteAllFiles } from "$lib/apis/files";
	import ResetUploadDirConfirmDialog from "$lib/components/common/ConfirmDialog.svelte";
	import ResetVectorDBConfirmDialog from "$lib/components/common/ConfirmDialog.svelte";
	import Tooltip from "$lib/components/common/Tooltip.svelte";
	import MultiSelect from "svelte-multiselect";
	import Spinner from "$lib/components/common/Spinner.svelte";

	const i18n = getContext("i18n");

	interface ServiceOption {
		label: string;
		value: number;
		[key: string]: any; // Added for compatibility with MultiSelect's internal type checks
	}

	// New code block
	const llmOptions = ["gpt-4o", "gpt-3.5-turbo", "ollama"];

	const serviceOptions: ServiceOption[] = [
		{ label: "Auto-selection (default)", value: -1 },
		{ label: "Chess", value: 0 },
		{ label: "Update Vector Database", value: 1 },
		{ label: "Code Generation", value: 2 },
		{ label: "General Question Answering", value: 3 },
	];

	// let service = -1;
	// let service = [-1];
	let service: ServiceOption[] = [serviceOptions[0]];
	$: {
		console.log("--- service variable update ---");
		console.log("  Is Array:", Array.isArray(service));
		console.log("  Value:", service);
		console.log("-------------------------------");
	}

	// let service = [serviceOptions[0]]; // Default value for "Auto-selection"
	let generalLLM = "gpt-4o"; // Default value
	let generalQuantized = false; // Default for "Quantized"
	let generalSeed = 0; // Default for "Random Seed"
	let queryAnalyserLLM = "gpt-4o";
	let queryAnalyserQuantized = false;
	let sameAsAbove = false;
	let isGPTModel = generalLLM.startsWith("gpt"); // Detect if the selected model is a GPT model
	let isOllamaSelected = generalLLM === "ollama"; // Detect if 'ollama' is selected
	let isQueryAnalyserGPTModel = queryAnalyserLLM.startsWith("gpt");
	let isQueryAnalyserOllamaSelected = queryAnalyserLLM == "ollama";
	let ollamaModelName = ""; // Variable to hold the name of the Ollama model to download
	let QueryAnalyserOllamaModelName = "";
	let openaiApiKey = ""; // OpenAI API Key
	let documentFilePath = ""; // Default value for the document path
	let stockfishPath = ""; // Default value for the Stockfish path
	const formData = new FormData();
	let isFileSelected = false; // Flag to check if a file is selected
	let isLoading = false; // Flag to indicate loading state

	// Default value for Retrieve Score Threshold
	let CoSMICRAGTopK = 1;
	let CoSMICRAGRetrieveScoreThreshold = 0.7;

	// new code block ends here
	let showResetConfirm = false;
	let showResetUploadDirConfirm = false;

	// Watch for "Same as Above" checkbox
	$: if (sameAsAbove) {
		isQueryAnalyserGPTModel = isGPTModel;
		isQueryAnalyserOllamaSelected = isOllamaSelected;
		queryAnalyserLLM = generalLLM;
		QueryAnalyserOllamaModelName = ollamaModelName;
		queryAnalyserQuantized = generalQuantized;
	}

	// Update function for LLM selection
	async function updateLLMSelection() {
		// Detect if the selected LLM is a GPT model
		isGPTModel = generalLLM.startsWith("gpt");

		// Detect if the selected LLM is explicitly 'ollama'
		isOllamaSelected = generalLLM === "ollama";

		console.log("LLM updated successfully:", generalLLM);
	}

	// Update function for LLM selection
	async function updateQueryAnalyserLLMSelection() {
		// Detect if the selected LLM is a GPT model
		isQueryAnalyserGPTModel = queryAnalyserLLM.startsWith("gpt");

		// Detect if the selected LLM is explicitly 'ollama'
		isQueryAnalyserOllamaSelected = queryAnalyserLLM === "ollama";
	}

	// Update function for OpenAI API Key
	async function updateOpenAIKey() {
		if (!openaiApiKey) {
			console.error("API Key cannot be empty.");
		}
	}

	// Function to save the Ollama model name
	async function updateOllamaModelName() {
		if (!ollamaModelName) {
			console.error("No Ollama model name provided.");
		}
		console.log("Ollama model name updated successfully:", ollamaModelName);
	}


	function loadServiceFromConfigs(configs: any) {
		const loadedServiceValue = configs["service"];
		if (Array.isArray(loadedServiceValue)) {
			// If it's an array of numbers, filter serviceOptions to match
			service = serviceOptions.filter((option) =>
				loadedServiceValue.includes(option.value),
			);
		} else if (typeof loadedServiceValue === "number") {
			// If it's a single number, find the corresponding ServiceOption
			service = serviceOptions.filter(
				(option) => option.value === loadedServiceValue,
			);
		} else {
			// Fallback for unexpected types, default to Auto-selection
			console.warn(
				"Unexpected type for service in cosmic_configs:",
				loadedServiceValue,
			);
			service = [serviceOptions[0]];
		}
	}

	// Function to handle file selection
	function handleFileSelection(event) {
		const files = event.target.files;
		if (files && files.length > 0) {
			documentFilePath = files[0].path || files[0].name; // Use the file path or name
			console.log("Selected file path:", documentFilePath);
		}
	}

	// Function to handle folder selection
	function handleFolderSelection(event) {
		const folders = event.target.files;
		console.log("Selected folders:", event);
		if (folders && folders.length > 0) {
			documentFilePath = folders[0].webkitRelativePath.split("/")[0]; // Get folder path
			console.log("Selected folder path:", documentFilePath);
		}
	}

	// Function to handle Stockfish file selection
	function handleStockfishSelection(event) {
		event.preventDefault(); // Prevent default behavior
		const file = event.target.files[0];
		console.log("Selected Stockfish file:", file, file.type);

		if (file) {
			stockfishPath = file.name; // Use the file path or name
			console.log("Selected Stockfish path:", stockfishPath);
			formData.append("file", file); // Append to FormData
			isFileSelected = true; // Set the flag to true
		}
	}

	async function updateCoSMICRAGRetrieveScoreThreshold() {
		// Ensure the value is within range
		if (
			CoSMICRAGRetrieveScoreThreshold < 0 ||
			CoSMICRAGRetrieveScoreThreshold > 1
		) {
			console.error("Value must be between 0 and 1.");
		}
		console.log(
			"RAG relevance threshold updated successfully:",
			CoSMICRAGRetrieveScoreThreshold,
		);
	}

	// Handler to update Quantized value
	async function updateQuantized() {
		console.log("Quantized updated successfully:", generalQuantized);
	}

	// Handler to update Random Seed value
	async function updategeneralSeed() {
		// Ensure the value is a non-negative integer
		if (generalSeed < 0 || !Number.isInteger(generalSeed)) {
			console.error("Random seed must be a non-negative integer.");
		}
		console.log("Random seed updated successfully:", generalSeed);
	}

	const submitHandler = async () => {
		isLoading = true;
		let general_llm_name = generalLLM;

		if (isOllamaSelected) {
			general_llm_name = `${generalLLM}:${ollamaModelName}`;
		}

		let query_analyser_llm_name = queryAnalyserLLM;

		if (isQueryAnalyserOllamaSelected) {
			if (sameAsAbove) {
				query_analyser_llm_name = general_llm_name;
			} else {
				query_analyser_llm_name = `${queryAnalyserLLM}:${QueryAnalyserOllamaModelName}`;
			}
		}

		try {
			const res = await updateCoSMICConfig(localStorage.token, {
				llm_name: general_llm_name,
				is_quantized: generalQuantized,
				seed: generalSeed,
				doc_directory: documentFilePath, // TODO
				document_path: documentFilePath, // TODO
				service: service.map((s) => s.value),
				// service: service,
				sameasabove: sameAsAbove,
				query_analyser: {
					llm_name: query_analyser_llm_name,
					is_quantized: queryAnalyserQuantized,
				},
				rag: {
					top_k: CoSMICRAGTopK,
					retrieve_score_threshold: CoSMICRAGRetrieveScoreThreshold,
					vector_db_path: "", // TODO
				},
				chess: {
					stockfish_path: stockfishPath,
				},
				openai: {
					api_key: openaiApiKey,
				},
			});

			if (isFileSelected) {
				const fileRes = await uploadChessFile(
					localStorage.token,
					formData,
				);
				if (fileRes.status === "success") {
					console.log("File uploaded successfully");
					isFileSelected = false; // Reset the flag after successful upload
					formData.delete("file"); // Clear the FormData
				} else {
					console.error("Error uploading file:", fileRes);
				}
			}

			if (res.status === "success") {
				console.log("Configs saved successfully");
				dispatch("save");
			} else {
				console.log("Error, updateCoSMICConfig failed.");
			}
			isLoading = false;
		} catch (error) {
			isLoading = false;
			console.error("Error updating CoSMIC configs:", error);
			toast.error(`Error updating CoSMIC configs: ${error}`);
		}
	};

	onMount(async () => {
		isLoading = true;
		const cosmic_configs = await getCoSMICConfig(localStorage.token);

		if (cosmic_configs) {
			generalLLM = cosmic_configs["llm_name"];

			if (generalLLM.startsWith("ollama")) {
				const words = generalLLM.split(":");
				generalLLM = words[0];
				ollamaModelName = words[1];
			}

			updateLLMSelection();

			generalQuantized = cosmic_configs["is_quantized"];
			generalSeed = cosmic_configs["seed"];
			documentFilePath = cosmic_configs["doc_directory"];

			const loadedService = cosmic_configs["service"];

			if (Array.isArray(loadedService)) {
				service = serviceOptions.filter((o) =>
					loadedService.includes(o.value),
				);
			} else if (typeof loadedService === "number") {
				service = serviceOptions.filter(
					(o) => o.value === loadedService,
				);
			} else {
				// Fallback for unexpected types, keep type consistent as ServiceOption[]
				console.warn(
					"Unexpected type for service in cosmic_configs:",
					loadedService,
				);
				service = []; //  keep it an empty array instead of [-1]
			}

			queryAnalyserLLM = cosmic_configs["query_analyser"]["llm_name"];

			if (queryAnalyserLLM.startsWith("ollama")) {
				const query_words = queryAnalyserLLM.split(":");
				queryAnalyserLLM = query_words[0];  
				QueryAnalyserOllamaModelName = query_words[1];
			}

			updateQueryAnalyserLLMSelection();

			queryAnalyserQuantized =
				cosmic_configs["query_analyser"]["is_quantized"];
			CoSMICRAGTopK = cosmic_configs["rag"]["topk"];
			CoSMICRAGRetrieveScoreThreshold =
				cosmic_configs["rag"]["retrieve_score_threshold"];
			stockfishPath = cosmic_configs["chess"]["stockfish_path"];
			sameAsAbove = cosmic_configs["sameasabove"];
			openaiApiKey = cosmic_configs["OPENAI_API_KEY"];
		}
		isLoading = false;
	});
</script>

<ResetUploadDirConfirmDialog
	bind:show={showResetUploadDirConfirm}
	on:confirm={async () => {
		const res = await deleteAllFiles(localStorage.token).catch((error) => {
			toast.error(error);
			return null;
		});

		if (res) {
			toast.success($i18n.t("Success"));
		}
	}}
/>

<ResetVectorDBConfirmDialog
	bind:show={showResetConfirm}
	on:confirm={() => {
		const res = resetVectorDB(localStorage.token).catch((error) => {
			toast.error(error);
			return null;
		});

		if (res) {
			toast.success($i18n.t("Success"));
		}
	}}
/>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={() => {
		submitHandler();
	}}
>
	<div class=" space-y-2.5 overflow-y-scroll scrollbar-hidden h-full pr-1.5">
		<div class="flex flex-col gap-0.5">
			<div
				class=" mb-2 text-2xl font-bold text-gray-900 dark:text-gray-300"
			>
				{$i18n.t("OpenSI-CoSMIC Settings")}
			</div>

			{#if isLoading}
				<Spinner className="size-6" />
			{:else}
				<section>
					<!-- General -->
					<section class="mb-4">
						<h2
							class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300"
						>
							General
						</h2>

						<div class="field">
							<label
								for="llm-select"
								class="mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
								>Choose an LLM</label
							>
							<div class="flex w-full">
								<select
									id="llm-select"
									bind:value={generalLLM}
									on:change={updateLLMSelection}
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
								>
									{#each llmOptions as llm}
										<option
											value={llm}
											class="bg-gray-100 dark:bg-gray-700"
										>
											{llm}
										</option>
									{/each}
								</select>
							</div>
						</div>

						<!-- OpenAI API Key Section -->
						{#if isGPTModel}
							<div class="mb-4">
								<label
									for="openai-api-key"
									class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
								>
									OpenAI API Key (required for GPT models and
									will be securely stored)
								</label>
								<input
									id="openai-api-key"
									type="password"
									bind:value={openaiApiKey}
									on:change={updateOpenAIKey}
									class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
									placeholder="Enter your OpenAI API Key"
								/>
							</div>
						{/if}

						<!-- Ollama Model Input Section -->
						{#if isOllamaSelected}
							<div class="mb-4">
								<label
									for="ollama-model-name"
									class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
								>
									Pull a model from
									<a
										href="https://ollama.com/library"
										target="_blank"
										class="text-blue-600 hover:underline dark:text-blue-400"
									>
										Ollama.com
									</a>
								</label>
								<input
									id="ollama-model-name"
									type="text"
									bind:value={ollamaModelName}
									on:change={updateOllamaModelName}
									class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
									placeholder="Enter the name of the Ollama model to download"
								/>
								<p
									class="mt-2 text-sm text-gray-500 dark:text-gray-400"
								></p>
							</div>
						{/if}

						<!-- Quantized Section -->
						<div class="mb-4">
							<label
								for="quantized"
								class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								Quantized
							</label>
							<div class="flex items-center space-x-2">
								<input
									id="quantized"
									type="checkbox"
									bind:checked={generalQuantized}
									on:change={updateQuantized}
									class="rounded border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 focus:ring-blue-500 focus:border-blue-500"
								/>
								<span
									class="text-sm text-gray-500 dark:text-gray-300"
								>
									Enable quantized model
								</span>
							</div>
						</div>

						<!-- Random Seed Section -->
						<div class="mb-4">
							<label
								for="random-seed"
								class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								Random Seed for LLM (enter an integer value no
								less than 0)
							</label>
							<input
								id="random-seed"
								type="number"
								min="0"
								step="1"
								bind:value={generalSeed}
								on:change={updategeneralSeed}
								class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
							/>
						</div>

						<!-- Service Selection Section -->
						<div class="mb-4">
							<label
								for="service-selection"
								class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								Select a Service
							</label>
							<MultiSelect
								id="service-selection"
								options={serviceOptions}
								bind:selected={service}
								outerDivClass="!w-full !p-2.5 !text-sm !rounded-lg !bg-gray-50 !dark:bg-gray-850 !dark:border-gray-700 !dark:text-gray-300 !focus:ring-blue-500 !focus:border-blue-500"
								liOptionClass="bg-gray-100 dark:bg-gray-700"
							/>
							<!-- <select
								id="service-selection"
								bind:value={service}
								class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
							>
								{#each serviceOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select> -->

							<!-- <select
								id="service-selection"
								multiple
								on:change={handleMultiSelectChange}
								class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
							>
								{#each serviceOptions as option}
									<option
										value={option.value}
										selected={service.includes(
											option.value,
										)}
									>
										{option.label}
									</option>
								{/each}
							</select> -->
						</div>
					</section>
				</section>

				<!-- Query Analyser Section -->
				<section>
					<h2 class="text-lg font-medium">Query Analyser</h2>
					<div class="space-y-3">
						<!-- Same as Above Checkbox -->
						<div>
							<input
								type="checkbox"
								class="rounded"
								bind:checked={sameAsAbove}
							/>
							<label class="mb-1.5 text-sm font-medium"
								>Same as Above</label
							>
						</div>

						<!-- Choose LLM -->
						<div class="mb-4">
							<label
								for="query-analyser-llm-select"
								class="mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								Choose an LLM
							</label>
							<div class="flex w-full">
								<select
									id="query-analyser-llm-select"
									bind:value={queryAnalyserLLM}
									on:change={updateQueryAnalyserLLMSelection}
									disabled={sameAsAbove}
									class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
								>
									{#each llmOptions as llm}
										<option
											value={llm}
											class="bg-gray-100 dark:bg-gray-700"
										>
											{llm}
										</option>
									{/each}
								</select>
							</div>
						</div>

						<!-- OpenAI API Key Section -->
						{#if isQueryAnalyserGPTModel && !isGPTModel}
							<div class="mb-4">
								<label
									for="openai-api-key"
									class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
								>
									OpenAI API Key (required for GPT models and
									will be securely stored)
								</label>
								<input
									id="openai-api-key"
									type="password"
									bind:value={openaiApiKey}
									on:change={updateOpenAIKey}
									disabled={sameAsAbove}
									class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
									placeholder="Enter your OpenAI API Key"
								/>
							</div>
						{/if}

						<!-- Ollama Model Input Section -->
						{#if isQueryAnalyserOllamaSelected}
							<div class="mb-4">
								<label
									for="query-analyser-ollama-model-name"
									class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
								>
									Pull a model from
									<a
										href="https://ollama.com/library"
										target="_blank"
										class="text-blue-600 hover:underline dark:text-blue-400"
									>
										Ollama.com
									</a>
								</label>
								<input
									id="query-analyser-ollama-model-name"
									type="text"
									bind:value={QueryAnalyserOllamaModelName}
									disabled={sameAsAbove}
									class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
									placeholder="Enter the name of the Ollama model to download"
								/>
								<p
									class="mt-2 text-sm text-gray-500 dark:text-gray-400"
								></p>
							</div>
						{/if}

						<!-- Quantized -->
						<div class="mb-4">
							<label
								for="quantized_query_analyser"
								class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								Quantized
							</label>
							<div class="flex items-center space-x-2">
								<input
									id="quantized_query_analyser"
									type="checkbox"
									bind:checked={queryAnalyserQuantized}
									class="rounded border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 focus:ring-blue-500 focus:border-blue-500"
									disabled={sameAsAbove}
								/>
								<span
									class="text-sm text-gray-500 dark:text-gray-300"
								>
									Enable quantized model
								</span>
							</div>
						</div>
					</div>
				</section>

				<!-- Chess Section -->
				<section class="mb-4">
					<h2
						class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300"
					>
						Chess
					</h2>

					<!-- Stockfish Path Subsection -->
					<div class="mb-4">
						<label
							for="stockfish-path"
							class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
						>
							Select the Stockfish executable file
						</label>
						<div class="flex items-center space-x-2">
							<!-- Text input to display the selected path -->
							<input
								id="stockfish-path"
								type="text"
								bind:value={stockfishPath}
								class="flex-1 block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
								readonly
								placeholder="No path selected"
							/>
							<!-- Button to select the Stockfish executable -->
							<button
								type="button"
								class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 dark:bg-blue-500 dark:hover:bg-blue-600 focus:outline-none dark:focus:ring-blue-800"
								on:click={() =>
									document
										.getElementById("stockfish-input")
										.click()}
							>
								Browse
							</button>
						</div>
						<!-- Hidden file input -->
						<input
							id="stockfish-input"
							type="file"
							class="hidden"
							on:change={handleStockfishSelection}
						/>
					</div>
				</section>

				<!-- RAG -->
				<section class="mb-4">
					<h2
						class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300"
					>
						RAG
					</h2>

					<div class="flex flex-col w-full">
						<div class="flex items-center space-x-1.5 mb-1">
							<div
								class="text-xs font-medium min-w-fit text-gray-900 dark:text-gray-300"
							>
								{$i18n.t("Top-K")}
							</div>
							<Tooltip
								content={$i18n.t(
									"Specifies how many of the most similar results are fetched from the vector database.",
								)}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-5 h-5 text-gray-700 dark:text-gray-300"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
									/>
								</svg>
							</Tooltip>
						</div>

						<div class="self-center w-full">
							<input
								class="w-full rounded-lg py-1.5 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
								type="number"
								placeholder={$i18n.t("Enter Top K")}
								bind:value={CoSMICRAGTopK}
								autocomplete="off"
								min="0"
							/>
						</div>
					</div>

					<!-- Retrieve Score Threshold Subsection -->
					<div class="mb-4">
						<!-- Flex container for title and tooltip -->
						<div class="flex items-center space-x-1.5 mb-1">
							<label
								for="retrieve-score-threshold"
								class="text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								Retrieve Score Threshold (enter a value between
								0 and 1, default is 0.7)
							</label>
							<Tooltip
								content={$i18n.t(
									"Defines the minimum similarity score a document must have to be included in the retrieved results. A higher threshold ensures more relevant results, while a lower threshold increases recall by including less relevant results. Recommended range: 0.5 - 0.9.",
								)}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-5 h-5 text-gray-700 dark:text-gray-300"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
									/>
								</svg>
							</Tooltip>
						</div>

						<input
							id="retrieve-score-threshold"
							type="number"
							min="0"
							max="1"
							step="0.01"
							bind:value={CoSMICRAGRetrieveScoreThreshold}
							on:change={updateCoSMICRAGRetrieveScoreThreshold}
							class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>
				</section>
			{/if}
		</div>
	</div>

	<div class="flex justify-end text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			type="submit"
			disabled={isLoading}
		>
			{$i18n.t("Save")}
		</button>
	</div>
</form>
