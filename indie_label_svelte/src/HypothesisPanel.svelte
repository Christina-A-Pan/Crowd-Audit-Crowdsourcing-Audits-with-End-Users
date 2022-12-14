<script lang="ts">
    import { onMount } from "svelte";
    import ClusterResults from "./ClusterResults.svelte";
    import HelpTooltip from "./HelpTooltip.svelte";

    import Button, { Label } from "@smui/button";
    import Textfield from '@smui/textfield';
    import { user } from './stores/cur_user_store.js';
    import { error_type } from './stores/error_type_store.js';
    import { new_evidence } from './stores/new_evidence_store.js';
    import { open_evidence } from './stores/open_evidence_store.js';
    import { topic_chosen } from './stores/cur_topic_store.js';
    
    import Drawer, {
        AppContent,
        Content,
        Header,
        Title,
        Subtitle,
    } from '@smui/drawer';
    import List, { Item, Text, Graphic, PrimaryText, SecondaryText } from '@smui/list';
    import LinearProgress from "@smui/linear-progress";
    import CircularProgress from '@smui/circular-progress';
    import Checkbox from '@smui/checkbox';
    import FormField from '@smui/form-field';
    import IconButton from "@smui/icon-button";
    import{ Wrapper } from '@smui/tooltip';
    import Radio from '@smui/radio';
    import Switch from '@smui/switch';

    export let model;
    // export let topic;
    export let user_dialog_open;

    let all_reports = [];

    let cur_user;
    user.subscribe(value => {
		cur_user = value;
	});

    let cur_topic;
    topic_chosen.subscribe(value => {
		cur_topic = value;
	});

    // Handle routing
    let searchParams = new URLSearchParams(window.location.search);
    let scaffold_method = searchParams.get("scaffold");
    let topic_vis_method = searchParams.get("topic_vis_method");

    // TODO: connect to selected["error_type"] so changes on main panel affect report panel
    // let cur_error_type;
    // error_type.subscribe(value => {
	// 	cur_error_type = value;
	// });

    // Handle drawer
    let open = false;
    let selected = null;
    let promise = Promise.resolve(null);
    let editTitle = false;
    let editErrorType = false;
    let unfinished_count = 0;
    
    function setActive(value: string) {
        selected = value;
        // Set local and store value of open evidence to selected report's
        cur_open_evidence = selected["evidence"];
        open_evidence.update((value) => cur_open_evidence);
        let isolated_topic = selected["title"].replace(/^(Topic: )/,'');
        console.log("selected title", selected["title"]);
        console.log(selected);

        // Close panel
        open = false;

        // Update topic if in personal mode
        if (scaffold_method == "personal" || scaffold_method == "personal_group" || scaffold_method == "personal_test" || scaffold_method == "tutorial") {
            topic_chosen.update((value) => isolated_topic);
        }
    }

    onMount(async () => {
        promise = getReports();
    });

    async function getReports() {
        if (model == "" || model == undefined){
            return [];
        }
        let req_params = {
            cur_user: cur_user,
            scaffold_method: scaffold_method,
            model: model,
            topic_vis_method: topic_vis_method,
        };
        let params = new URLSearchParams(req_params).toString();
        const response = await fetch("./get_reports?" + params);
        const text = await response.text();
        const data = JSON.parse(text);
        all_reports = data["reports"]
        // Select first report initially
        selected = all_reports[0];
        setActive(selected);
        cur_open_evidence = selected["evidence"];
        unfinished_count = all_reports.filter(item => !item.complete_status).length
        return all_reports;
    }

    // Handle evidence saving
    let cur_open_evidence = [];
    new_evidence.subscribe(value => {
        if (value != []) {
            // Check if any values with the same ID exist
            for (let i = 0; i < cur_open_evidence.length; i++) {
                if (cur_open_evidence[i]["id"] == value["id"]) {
                    return; // If so, don't add the item
                }
            }
            cur_open_evidence = cur_open_evidence.concat(value); // add new evidence item

            // Add to open evidence in store
            open_evidence.update((value) => cur_open_evidence);
            // Save to selected value
            if (selected != null) {
                selected["evidence"] = cur_open_evidence;
            }
        }
	});

    // Handle evidence removal
    open_evidence.subscribe(value => {
        if ((value != cur_open_evidence) && (value.length < cur_open_evidence.length)) {
            // Update local open evidence
            cur_open_evidence = value;
            // Save to selected value
            if (selected != null) {
                selected["evidence"] = cur_open_evidence;
            }
        }
	});

    let promise_save = Promise.resolve(null);
    function handleSaveReport() {
        promise_save = saveReport();
    }

    async function saveReport() {
        let req_params = {
            cur_user: cur_user,
            reports: JSON.stringify(all_reports),
            scaffold_method: scaffold_method,
        };
        let params = new URLSearchParams(req_params).toString();
        const response = await fetch("./save_reports?" + params);
        const text = await response.text();
        const data = JSON.parse(text);
        return data;
    }

    function handleNewReport() {
        let new_report = {
            title: "",
            error_type: "",
            evidence: [],
            text_entry: "",
            complete_status: false,
        };
        all_reports = all_reports.concat(new_report);
        promise = Promise.resolve(all_reports);
        // Open this new report
        selected = all_reports[all_reports.length - 1];
        cur_open_evidence = selected["evidence"];
        selected["complete_status"] = false;
        unfinished_count = all_reports.filter(item => !item.complete_status).length
    }

    function handleDeleteReport() {
        // Remove selected item from reports
        all_reports = all_reports.filter(item => item != selected);
        promise = Promise.resolve(all_reports);
        selected  = all_reports[0];
        cur_open_evidence = selected["evidence"];
        unfinished_count = all_reports.filter(item => !item.complete_status).length
    }

    function handleMarkComplete() {
        selected["complete_status"] = !selected["complete_status"];
        unfinished_count = all_reports.filter(item => !item.complete_status).length
        handleSaveReport(); // Auto-save report
    }

    // Error type
    let error_type_options = [
        {
            "opt": 'Both', 
            "descr": '(System is under- or over-sensitive)', 
            "help": "View both types of potential system errors"
        },
        {
            "opt": 'System is under-sensitive', 
            "descr": '(Incorrectly rates as non-toxic)', 
            "help": "Focus on system errors where the system labeled content as Non-toxic when it should have been labeled as Toxic."
        },
        {
            "opt": 'System is over-sensitive', 
            "descr": '(Incorrectly rates as toxic)', 
            "help": "Focus on system errors where the system labeled content as Toxic when it should have been labeled as Non-toxic."
        },
        {
            "opt": 'Show errors and non-errors', 
            "descr": '', 
            "help": "Also show cases that are not likely to be potential errors"
        },
    ]

    // Save current error type
    async function updateErrorType() {    
        // Update error type on main page to be the selected error type
		// error_type.update((value) => cur_error_type);
        // selected["error_type"] = cur_error_type;
        editErrorType = false;
	}

</script>

<div class="hypothesis_panel">
    <div class="panel_header">
        <div class="panel_header_content">
            <div class="page_header">
                <!-- <span class="page_title">IndieLabel</span> -->
                <img src="/logo.png" style="height: 60px; padding: 0px 20px;" alt="IndieLabel" />
                <Button on:click={() => (user_dialog_open = true)} class="user_button" color="secondary" style="margin: 12px 10px;" >
                    <Label>User: {cur_user}</Label>
                </Button>
            </div>
            <div class="hypotheses_header">
                <h5 style="float: left; margin: 0; padding: 5px 20px;">Your Audit Reports</h5>
                <Button 
                    on:click={() => (open = !open)}
                    color="primary"
                    style="float: right; padding: 10px; margin-right: 10px;"
                >
                    {#if open}
                    <Label>Close</Label>
                    {:else}
                        {#key unfinished_count}
                        <Label>Unfinished reports ({unfinished_count})</Label>
                        {/key}
                    {/if}
                </Button>
            </div>
        </div>
    </div>

    <div class="panel_contents">  
        <!-- Drawer -->
        {#await promise}
            <div class="app_loading_fullwidth">
                <LinearProgress indeterminate />
            </div>
        {:then reports}
            {#if reports}
            <div class="drawer-container">
                {#key open}
                <Drawer variant="dismissible" bind:open>
                    <Header>
                        <Title>Your Reports</Title>
                        <Subtitle>Select a report to view.</Subtitle>
                    </Header>
                    <Content>
                        <List twoLine>
                            {#each reports as report}
                                <Item
                                    href="javascript:void(0)"
                                    on:click={() => setActive(report)}
                                    activated={selected === report}
                                >   
                                    {#if report["complete_status"]}
                                    <Graphic class="material-icons" aria-hidden="true">task_alt</Graphic>
                                    {:else}
                                    <Graphic class="material-icons" aria-hidden="true">radio_button_unchecked</Graphic>
                                    {/if}
                                    <Text>
                                        <PrimaryText>
                                            {report["title"]}
                                        </PrimaryText>
                                        <SecondaryText>
                                            {report["error_type"]}
                                        </SecondaryText>
                                    </Text>
                                </Item>
                            {/each}
                        </List>
                    </Content>
                </Drawer>
                {/key}
                <AppContent class="app-content">
                    <main class="main-content">
                        {#if selected}
                        <div class="head_6_highlight">
                            Current Report
                        </div>
                        <div class="panel_contents2">
                            <!-- Title -->
                            <div class="spacing_vert">
                                <div class="edit_button_row">
                                    {#if editTitle}
                                        <div class="edit_button_row_input">
                                            <Textfield
                                                bind:value={selected["title"]}
                                                label="Your report title"
                                                input$rows={4}
                                                textarea
                                                variant="outlined"
                                                style="width: 100%;"
                                                helperLine$style="width: 100%;"
                                            />
                                        </div>
                                        <div>
                                            <IconButton class="material-icons grey_button" size="button" on:click={() => (editTitle = false)}>
                                                check
                                            </IconButton>
                                        </div>
                                    {:else}
                                        {#if selected["title"] != ""}
                                            <div class="head_5">
                                                {selected["title"]}
                                            </div>
                                        {:else}
                                            <div class="grey_text">Enter a report title</div>
                                        {/if}

                                        <div>
                                            <IconButton class="material-icons grey_button" size="button" on:click={() => (editTitle = true)}>
                                                create
                                            </IconButton>
                                        </div>
                                    {/if}
                                </div>
                            </div>

                            <!-- Error type -->
                            <div class="spacing_vert_40">
                                <div class="head_6">
                                    <b>Error Type</b> 
                                </div>
                                <div class="edit_button_row">
                                    {#if editErrorType}
                                        <div>
                                            {#each error_type_options as e}
                                                <div style="display: flex; align-items: center;">
                                                    <!-- <Wrapper rich>
                                                        <FormField>
                                                            <Radio bind:group={selected["error_type"]} value={e.opt} on:change={updateErrorType} color="secondary" />
                                                            <span slot="label">
                                                                {e.opt}
                                                                <IconButton class="material-icons" size="button" disabled>help_outline</IconButton>
                                                            </span>
                                                        </FormField>
                                                        <HelpTooltip text={e.help} />
                                                    </Wrapper> -->

                                                    <FormField>
                                                        <Radio bind:group={selected["error_type"]} value={e.opt} on:change={updateErrorType} color="secondary" />
                                                        <span slot="label">
                                                            <b>{e.opt}</b> {e.descr}
                                                        </span>
                                                    </FormField>
                                                </div>
                                            {/each}
                                        </div>
                                        <!-- <div>
                                            <IconButton class="material-icons grey_button" size="button" on:click={() => (editErrorType = false)}>
                                                check
                                            </IconButton>
                                        </div> -->
                                    {:else}
                                        {#if selected["error_type"] != ""}
                                            <div>
                                                <p>{selected["error_type"]}</p>
                                            </div>
                                        {:else}
                                            <div class="grey_text">Select an error type</div>
                                        {/if}
                                        
                                        <div>
                                            <IconButton class="material-icons grey_button" size="button" on:click={() => (editErrorType = true)}>
                                                create
                                            </IconButton>
                                        </div>
                                    {/if}
                                </div>
                            </div>
                            
                            <!-- Evidence -->
                            <div class="spacing_vert_40">
                                <div class="head_6">
                                    <b>Evidence</b>
                                </div>
                                {#key cur_open_evidence}
                                <div>
                                    {#if cur_open_evidence.length > 0}
                                    <ClusterResults 
                                        cluster={cur_topic} 
                                        model={model} 
                                        data={{"cluster_comments": cur_open_evidence}} 
                                        show_vis={false} 
                                        show_checkboxes={false} 
                                        table_width_pct={100} 
                                        rowsPerPage={25} 
                                        table_id={"panel"}
                                    />
                                    {:else}
                                        <p class="grey_text">
                                            Add examples from the main panel to see them here!
                                        </p>
                                    {/if}
                                </div>
                                {/key}
                            </div>

                            <div class="spacing_vert_60">
                                <div class="head_6">
                                    <b>Summary/Suggestions</b>
                                </div>
                                <div class="spacing_vert">
                                    <Textfield
                                        style="width: 100%;"
                                        helperLine$style="width: 100%;"
                                        input$rows={8}
                                        textarea
                                        bind:value={selected["text_entry"]}
                                        label="My current hunch is that..."
                                    >
                                    </Textfield>
                                </div>
                                
                            </div>

                            <div class="spacing_vert_40">
                                <div class="head_6">
                                    <b>Mark report as complete?</b>
                                    <FormField>
                                        <Checkbox checked={selected["complete_status"]} on:change={handleMarkComplete} />
                                    </FormField>
                                </div>
                                
                            </div>
                        </div>
                        {/if}
                    </main>
                </AppContent>
            </div>
            {/if}
        {:catch error}
            <p style="color: red">{error.message}</p>
        {/await}
    </div>

    <div class="panel_footer">
        <div class="panel_footer_contents">
            

            <Button 
                on:click={handleNewReport} 
                variant="outlined" 
                color="secondary"
                style=""
            >
                <Label>New</Label>
            </Button>

            <Button 
                on:click={handleDeleteReport} 
                variant="outlined" 
                color="secondary"
                style=""
            >
                <Label>Delete</Label>
            </Button>

            <Button 
                on:click={handleSaveReport} 
                variant="outlined" 
                color="secondary"
            >
                <Label>Save</Label>
            </Button>

            <div>
                <span style="color: grey"><i>Last saved:
                {#await promise_save}
                    <CircularProgress style="height: 32px; width: 32px;" indeterminate />
                {:then result}
                    {#if result}
                     {new Date().toLocaleTimeString()}
                    {:else}
                     ???
                    {/if}
                {:catch error}
                    <p style="color: red">{error.message}</p>
                {/await}
                </i></span>
            </div>
        </div>
    </div>

    <!-- TEMP -->
    <!-- {#key model}
        <div>Model: {model}</div> 
    {/key} -->
</div>

<style>
    /* Drawer */
    /* .drawer-container {
        position: relative;
        display: flex;
        height: 350px;
        max-width: 600px;
        border: 1px solid
        var(--mdc-theme-text-hint-on-background, rgba(0, 0, 0, 0.1));
        overflow: hidden;
        z-index: 0;
    }
    
    * :global(.app-content) {
        flex: auto;
        overflow: auto;
        position: relative;
        flex-grow: 1;
    }
    
    .main-content {
        overflow: auto;
        padding: 16px;
        height: 100%;
        box-sizing: border-box;
    } */

    .panel_contents {
        padding: 0 20px;
        overflow-y: auto;
        top: 150px;
        position: relative;
        height: 82%;
    }
    .panel_contents2 {
        padding-left: 10px;
    }

    .panel_header {
        position: fixed;
        width: 30%;
        border-bottom: 1px solid #d7d7d7; /* c5c5c5 */
        background: #f3f3f3;
        z-index: 11;
    }

    .panel_footer {
        position: fixed;
        width: 30%;
        border-top: 1px solid #d7d7d7;
        background: #f3f3f3;
        z-index: 11;
        bottom: 0;
        padding: 15px 0px;
    }
    .panel_footer_contents {
        /* padding: 0px 20px; */
        display: flex;
        justify-content: space-around;
        align-items: center;
    }

    :global(.mdc-button.user_button) {
        float: right;
        margin-right: 20px;
    }

    .page_header {
        width: 100%;
        background: #e3d6fd;
        /* padding: 21px 0; */
        /* border-bottom: 1px solid #e3d6fd; */
        padding: 10.5px 0;
        position: relative;
        display: inline-block;
    }

    .page_header:before {
        content: '';
        border-right: 1px solid rgb(0 0 0 / 7%);
        position: absolute;
        height: 80%;
        top: 10%;
        right: 0;
    }

    .hypotheses_header {
        display: inline-block;
        width: 100%;
        padding: 10px 0;
        vertical-align: middle;
    }
</style>
