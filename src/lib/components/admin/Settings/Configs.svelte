<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	import {
		getQuerySettings,
		updateQuerySettings,
		resetVectorDB,
		getEmbeddingConfig,
		updateEmbeddingConfig,
		getRerankingConfig,
		updateRerankingConfig,
		resetUploadDir,
		getRAGConfig,
		updateRAGConfig,
	} from '$lib/apis/retrieval';

	import {
		getCoSMICConfig,
		updateCoSMICConfig
	} from '$lib/apis/cosmic';

	import { knowledge, models } from '$lib/stores';
	import { getKnowledgeItems } from '$lib/apis/knowledge';
	import { uploadDir, deleteAllFiles, deleteFileById } from '$lib/apis/files';
	import ResetUploadDirConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import ResetVectorDBConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');

	// New code block
	const llmOptions = [
		"gpt-4o",
		"gpt-3.5-turbo",
		"ollama"
    ];

	let service = -1; // Default value for "Auto-selection"

	const serviceOptions = [
		{ label: "Auto-selection (default)", value: -1 },
		{ label: "Chess", value: 0 },
		{ label: "Update Vector Database", value: 1 },
		{ label: "Code Generation", value: 2 },
		{ label: "General Question Answering", value: 3 }
	];

    let generalLLM = "gpt-4o"; // Default value
	let generalQuantized = false; // Default for "Quantized"
	let generalSeed = 0;  // Default for "Random Seed"
	let queryAnalyserLLM = "gpt-4o";
    let queryAnalyserQuantized = false;
	let sameAsAbove = false;
	let isGPTModel = generalLLM.startsWith("gpt"); // Detect if the selected model is a GPT model
	let isOllamaSelected = generalLLM === "ollama"; // Detect if 'ollama' is selected
	let isQueryAnalyserOllamaSelected = queryAnalyserLLM == "ollama";
    let ollamaModelName = ""; // Variable to hold the name of the Ollama model to download
    let openaiApiKey = ""; // OpenAI API Key
	let huggingfaceToken = ""; // Hugging Face Token
	let documentFilePath = ""; // Default value for the document path
	let stockfishPath = ""; // Default value for the Stockfish path

	// Variables to track the selected LLM type
	// let isQueryAnalyserGPTModel = queryAnalyserLLM.startsWith("gpt");
    // let isQueryAnalyserOllamaSelected = queryAnalyserLLM === "ollama";

	// Default value for Retrieve Score Threshold
	let CoSMICLLMName = '';
	let CoSMICQueryAnalyserLLMName = '';
    let CoSMICRAGTopK = 1;
	let CoSMICRAGRetrieveScoreThreshold = 0.7;
	let CoSMICVectorDBPath = "";
	let CoSMICStockfishPath = "";

	// new code block ends here
	let scanDirLoading = false;
	let updateEmbeddingModelLoading = false;
	let updateRerankingModelLoading = false;
	let showResetConfirm = false;
	let showResetUploadDirConfirm = false;
	let embeddingEngine = '';
	let embeddingModel = '';
	let rerankingModel = '';
	let fileMaxSize = null;
	let fileMaxCount = null;
	let contentExtractionEngine = 'default';
	let tikaServerUrl = '';
	let showTikaServerUrl = false;
	let chunkSize = 0;
	let chunkOverlap = 0;
	let pdfExtractImages = true;
	let OpenAIKey = '';
	let OpenAIUrl = '';
	let OpenAIBatchSize = 1;

	let querySettings = {
		template: '',
		r: 0.0,
		k: 4,
		hybrid: false
	};
 

	// Watch for "Same as Above" checkbox
    $: if (sameAsAbove) {
		isQueryAnalyserOllamaSelected = isOllamaSelected;
		
		if (isQueryAnalyserOllamaSelected) {
			queryAnalyserLLM = `${generalLLM}:${ollamaModelName}`;
		} else {
			queryAnalyserLLM = generalLLM;
		}
        queryAnalyserQuantized = generalQuantized;
    }


	// Update function for LLM selection
	async function updateLLMSelection() {
		// Detect if the selected LLM is a GPT model
		isGPTModel = generalLLM.startsWith("gpt");


		// Detect if the selected LLM is explicitly 'ollama'
		isOllamaSelected = generalLLM === "ollama";

		// Send the selected LLM to the backend
		try {
			await updateQuerySettings({ llm: generalLLM });
			console.log("LLM updated successfully:", generalLLM);
		} catch (error) {
			console.error("Error updating LLM selection:", error);
		}
	}


	// Update function for OpenAI API Key
    async function updateOpenAIKey() {
	    if (!openaiApiKey) {
	        console.error("API Key cannot be empty.");
		    return;
	    }
    }

	
	// Function to save the Ollama model name
    async function updateOllamaModelName() {
		if (!ollamaModelName) {
			console.error("No Ollama model name provided.");
			return;
		}
		try {
			await updateQuerySettings({ ollama_model_name: ollamaModelName });
			console.log("Ollama model name updated successfully:", ollamaModelName);
		} catch (error) {
			console.error("Error updating Ollama model name:", error);
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
		if (folders && folders.length > 0) {
			documentFilePath = folders[0].webkitRelativePath.split("/")[0]; // Get folder path
			console.log("Selected folder path:", documentFilePath);
		}
	}


    // Save the selected path
	async function updateDocumentPath() {
		if (!documentFilePath) {
			console.error("No document path selected.");
			return;
		}
		try {
			await updateQuerySettings({ document_file_path: documentFilePath });
			console.log("Document File Path updated successfully:", documentFilePath);
		} catch (error) {
			console.error("Error updating document file path:", error);
		}
	}


	// Function to handle Stockfish file selection
	function handleStockfishSelection(event) {
		const files = event.target.files;
		if (files && files.length > 0) {
			stockfishPath = files[0].path || files[0].name; // Use the file path or name
			console.log("Selected Stockfish path:", stockfishPath);
		}
	}


	// Save the Stockfish path
	async function updateStockfishPath() {
		if (!stockfishPath) {
			console.error("No Stockfish path selected.");
			return;
		}
		try {
			await updateQuerySettings({ stockfish_path: stockfishPath });
			console.log("Stockfish Path updated successfully:", stockfishPath);
		} catch (error) {
			console.error("Error updating Stockfish path:", error);
		}
	}


	async function updateCoSMICRAGRetrieveScoreThreshold() {
		try {
			// Ensure the value is within range
			if (CoSMICRAGRetrieveScoreThreshold < 0 || CoSMICRAGRetrieveScoreThreshold > 1) {
				console.error("Value must be between 0 and 1.");
				return;
			}
			// await updateQuerySettings({ retrieve_score_threshold: retrieveScoreThreshold });
			console.log("RAG relevance threshold updated successfully:", CoSMICRAGRetrieveScoreThreshold);
		} catch (error) {
			console.error("Error updating Retrieve Score Threshold:", error);
		}
	}


	// Handler to update Quantized value
    async function updateQuantized() {
		try {
			await updateQuerySettings({ is_quantized: generalQuantized });
			console.log("Quantized updated successfully:", generalQuantized);
		} catch (error) {
			console.error("Error updating Quantized value:", error);
		}
    }


	// Handler to update Random Seed value
	async function updategeneralSeed() {
		try {
			// Ensure the value is a non-negative integer
			if (generalSeed < 0 || !Number.isInteger(generalSeed)) {
				console.error("Random Seed must be a non-negative integer.");
				return;
			}
			await updateQuerySettings({ random_seed: generalSeed });
			console.log("Random Seed updated successfully:", generalSeed);
		} catch (error) {
			console.error("Error updating Random Seed value:", error);
		}
	}


	// new code block ends here
	const embeddingModelUpdateHandler = async () => {
		if (embeddingEngine === '' && embeddingModel.split('/').length - 1 > 1) {
			toast.error(
				$i18n.t(
					'Model filesystem path detected. Model shortname is required for update, cannot continue.'
				)
			);
			return;
		}
		if (embeddingEngine === 'ollama' && embeddingModel === '') {
			toast.error(
				$i18n.t(
					'Model filesystem path detected. Model shortname is required for update, cannot continue.'
				)
			);
			return;
		}

		if (embeddingEngine === 'openai' && embeddingModel === '') {
			toast.error(
				$i18n.t(
					'Model filesystem path detected. Model shortname is required for update, cannot continue.'
				)
			);
			return;
		}

		if ((embeddingEngine === 'openai' && OpenAIKey === '') || OpenAIUrl === '') {
			toast.error($i18n.t('OpenAI URL/Key required.'));
			return;
		}

		console.log('Update embedding model attempt:', embeddingModel);

		updateEmbeddingModelLoading = true;
		const res = await updateEmbeddingConfig(localStorage.token, {
			embedding_engine: embeddingEngine,
			embedding_model: embeddingModel,
			...(embeddingEngine === 'openai'
				? {
						openai_config: {
							key: OpenAIKey,
							url: OpenAIUrl,
							batch_size: OpenAIBatchSize
						}
					}
				: {})
		}).catch(async (error) => {
			toast.error(error);
			await setEmbeddingConfig();
			return null;
		});
		updateEmbeddingModelLoading = false;

		if (res) {
			console.log('embeddingModelUpdateHandler:', res);
			if (res.status === true) {
				toast.success($i18n.t('Embedding model set to "{{embedding_model}}".', res), {
					duration: 1000 * 10
				});
			}
		}
	};


	const rerankingModelUpdateHandler = async () => {
		console.log('Update reranking model attempt:', rerankingModel);

		updateRerankingModelLoading = true;
		const res = await updateRerankingConfig(localStorage.token, {
			reranking_model: rerankingModel
		}).catch(async (error) => {
			toast.error(error);
			await setRerankingConfig();
			return null;
		});
		updateRerankingModelLoading = false;

		if (res) {
			console.log('rerankingModelUpdateHandler:', res);
			if (res.status === true) {
				if (rerankingModel === '') {
					toast.success($i18n.t('Reranking model disabled', res), {
						duration: 1000 * 10
					});
				} else {
					toast.success($i18n.t('Reranking model set to "{{reranking_model}}"', res), {
						duration: 1000 * 10
					});
				}
			}
		}
	};


	const submitHandler = async () => {
		await embeddingModelUpdateHandler();

		if (querySettings.hybrid) {
			await rerankingModelUpdateHandler();
		}

		if (contentExtractionEngine === 'tika' && tikaServerUrl === '') {
			toast.error($i18n.t('Tika Server URL required.'));
			return;
		}

		const res = await updateRAGConfig(localStorage.token, {
			pdf_extract_images: pdfExtractImages,
			file: {
				max_size: fileMaxSize === '' ? null : fileMaxSize,
				max_count: fileMaxCount === '' ? null : fileMaxCount
			},
			chunk: {
				chunk_overlap: chunkOverlap,
				chunk_size: 1234
			},
			content_extraction: {
				engine: contentExtractionEngine,
				tika_server_url: tikaServerUrl
			}
		});

		if (isOllamaSelected) {
			generalLLM = `${generalLLM}:${ollamaModelName}`;
		}

		await updateCoSMICConfig(localStorage.token, {
			llm_name: generalLLM,
			is_quantized: generalQuantized,
			seed: generalSeed,
			doc_directory: documentFilePath,  // TODO
			document_path: documentFilePath,  // TODO
			service: service,
			query_analyser: {
				llm_name: queryAnalyserLLM,
				is_quantized: queryAnalyserQuantized
			},
			rag: {
				top_k: CoSMICRAGTopK,
				retrieve_score_threshold: CoSMICRAGRetrieveScoreThreshold,
				vector_db_path: documentFilePath // TODO
			},
			chess: {
				stockfish_path: stockfishPath
			},
			openai: {
				api_key: openaiApiKey
			}
		});

		await updateQuerySettings(localStorage.token, querySettings);

		dispatch('save');
	};


	const setEmbeddingConfig = async () => {
		const embeddingConfig = await getEmbeddingConfig(localStorage.token);

		if (embeddingConfig) {
			embeddingEngine = embeddingConfig.embedding_engine;
			embeddingModel = embeddingConfig.embedding_model;

			OpenAIKey = embeddingConfig.openai_config.key;
			OpenAIUrl = embeddingConfig.openai_config.url;
			OpenAIBatchSize = embeddingConfig.openai_config.batch_size ?? 1;
		}
	};


	const setRerankingConfig = async () => {
		const rerankingConfig = await getRerankingConfig(localStorage.token);

		if (rerankingConfig) {
			rerankingModel = rerankingConfig.reranking_model;
		}
	};


	const toggleHybridSearch = async () => {
		querySettings.hybrid = !querySettings.hybrid;
		querySettings = await updateQuerySettings(localStorage.token, querySettings);
	};


	onMount(async () => {
		await setEmbeddingConfig();
		await setRerankingConfig();

		querySettings = await getQuerySettings(localStorage.token);
		await getRAGConfigxx(localStorage.token);
		const res = await getRAGConfig(localStorage.token);

		if (res) {
			pdfExtractImages = res.pdf_extract_images;

			chunkSize = res.chunk.chunk_size;
			chunkOverlap = res.chunk.chunk_overlap;

			contentExtractionEngine = res.content_extraction.engine;
			tikaServerUrl = res.content_extraction.tika_server_url;
			showTikaServerUrl = contentExtractionEngine === 'tika';

			fileMaxSize = res?.file.max_size ?? '';
			fileMaxCount = res?.file.max_count ?? '';

			await getCoSMICConfig(localStorage.token);
		}
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
			toast.success($i18n.t('Success'));
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
			toast.success($i18n.t('Success'));
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
			<div class=" mb-2 text-2xl font-bold text-gray-900 dark:text-gray-300">{$i18n.t('OpenSI-CoSMIC Settings')}</div>

			<section>
				<!-- General -->
				<section class="mb-4">
					<h2 class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300">General</h2>

					<div class="field">
						<label for="llm-select" class="mb-1 text-sm font-medium text-gray-900 dark:text-gray-300">Choose an LLM</label>
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

					<!-- OpenAI API Key Section -->
					{#if isGPTModel}
						<div class="mb-4">
							<label
								for="openai-api-key"
								class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
							>
								OpenAI API Key (required for GPT models and will be securely stored)
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
							<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
								
							</p>
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
							<span class="text-sm text-gray-500 dark:text-gray-300">
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
							Random Seed for LLM (enter an integer value no less than 0)
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
				</div>

				<!-- Service Selection Section -->
				<div class="mb-4">
					<label
						for="service-selection"
						class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
					>
						Select a Service
					</label>
					<select
						id="service-selection"
						bind:value={service}
						class="block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
					>
						{#each serviceOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>
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
						<label class="mb-1.5 text-sm font-medium">Same as Above</label>
					</div>

					<!-- Chose LLM -->
					<div>
						<label class="mb-1.5 text-sm font-medium text-gray-900 dark:text-gray-300">Choose an LLM</label>
						<select
							class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
							bind:value={queryAnalyserLLM}
							disabled={sameAsAbove}
						>
							<option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
							<option value="gpt-4o">gpt-4o</option>
							<option value="ollama">ollama</option>
						</select>
					</div>

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
							<span class="text-sm text-gray-500 dark:text-gray-300">
								Enable quantized model
							</span>
						</div>
					</div>
				</div>
			</section>

			<!-- Vector Database Section -->
			<section class="mt-6 mb-4">
				<h2 class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300">Vector Database</h2>

				<!-- Document File Path Subsection -->
				<div class="mb-4">
					<label
						for="document-file-path"
						class="block mb-1 text-sm font-medium text-gray-900 dark:text-gray-300"
					>
						Select a document or folder to use for the vector database
					</label>
					<div class="flex items-center space-x-2">
						<!-- Text input to display the selected path -->
						<input
							id="document-file-path"
							type="text"
							bind:value={documentFilePath}
							class="flex-1 block w-full p-2.5 text-sm rounded-lg border border-gray-300 bg-gray-50 dark:bg-gray-850 dark:border-gray-700 dark:text-gray-300 focus:ring-blue-500 focus:border-blue-500"
							readonly
							placeholder="No path selected"
						/>
						<!-- Button to select a file -->
						<button
							class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 dark:bg-blue-500 dark:hover:bg-blue-600 focus:outline-none dark:focus:ring-blue-800"
							on:click={() => document.getElementById('file-input').click()}
						>
							Browse File
						</button>
						<!-- Button to select a folder -->
						<button
							class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 focus:ring-4 focus:ring-green-300 dark:bg-green-500 dark:hover:bg-green-600 focus:outline-none dark:focus:ring-green-800"
							on:click={() => document.getElementById('folder-input').click()}
						>
							Browse Folder
						</button>
					</div>
					<!-- Hidden file input -->
					<input
						id="file-input"
						type="file"
						class="hidden"
						on:change={handleFileSelection}
					/>
					<!-- Hidden folder input -->
					<input
						id="folder-input"
						type="file"
						webkitdirectory
						class="hidden"
						on:change={handleFolderSelection}
					/>
				</div>
			</section>

			<!-- Chess Section -->
			<section class="mb-4">
  			    <h2 class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300">Chess</h2>

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
							class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 dark:bg-blue-500 dark:hover:bg-blue-600 focus:outline-none dark:focus:ring-blue-800"
							on:click={() => document.getElementById('stockfish-input').click()}
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
			    <h2 class="mb-2 text-lg font-medium text-gray-900 dark:text-gray-300">RAG</h2>

				<div class="flex flex-col w-full">
					<div class="flex items-center space-x-1.5 mb-1">
						<div class="text-xs font-medium min-w-fit text-gray-900 dark:text-gray-300">
							{$i18n.t('Top-K')}
						</div>
						<Tooltip content={$i18n.t('Specifies how many of the most similar results are fetched from the vector database.')}>
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
							placeholder={$i18n.t('Enter Top K')}
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
							Retrieve Score Threshold (enter a value between 0 and 1, default is 0.7)
						</label>
						<Tooltip content={$i18n.t('Defines the minimum similarity score a document must have to be included in the retrieved results. A higher threshold ensures more relevant results, while a lower threshold increases recall by including less relevant results. Recommended range: 0.5 - 0.9.')}>
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
		</div>
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class=" px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-gray-100 transition rounded-lg"
			type="submit"
		>
			{$i18n.t('Save')}
		</button>
	</div>
</form>