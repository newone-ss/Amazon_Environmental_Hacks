/**
 * Bhujal - Bilingual UI Localization (English & Hindi)
 * Numbers, coordinates, and rule IDs remain untranslated.
 */

export const TRANSLATIONS = {
  en: {
    brand_subtitle: 'AI for Heat & Water Resilience',
    demo_badge: 'Demo Data',
    search_placeholder: 'Search settlement or district...',
    all_states: 'All states',
    nav_map: 'Map',
    nav_field_data: 'Field Data',
    nav_reports: 'Reports',
    nav_about: 'About & Data',
    nav_help: 'Help',

    // Safety
    verdict_safe: 'CLEARED: SAFE TO BUILD',
    verdict_conditional: 'CONDITIONAL SAFETY VERDICT',
    verdict_rejected: 'REJECTED — NO STRUCTURE RECOMMENDED',
    safety_kicker: 'DETERMINISTIC SAFETY VERDICT',
    safety_rule_label: 'Triggered Rule IDs:',

    // Tabs
    tab_overview: 'Overview',
    tab_agents: 'AI Agents',
    tab_plan: 'Plan',
    tab_scenario: 'Scenario',
    tab_evidence: 'Evidence',
    agent_briefing_title: 'Multi-Agent Domain Intelligence',
    agent_consult_title: 'Interactive Lead Planner Consultation',
    ask_agent_placeholder: 'Ask Lead Planner Agent about this site (e.g. Can we build check dam?)...',
    agent_consult_btn: 'Consult Agent',


    // Scores
    score_recharge: 'Recharge Potential',
    score_heat: 'Heat-Water Vulnerability',
    score_spring: 'Spring Desiccation Risk',
    why_drivers: "Key Drivers ('Why?' Breakdown)",
    all_drivers: 'All drivers',
    top_drivers: 'Top 3 drivers',

    // Recommendations
    rec_title: 'RECOMMENDED ACTION',
    view_plan: 'View Detailed Work Plan',
    generate_dpr: 'Generate DPR Package (.ZIP)',
    open_report: 'Open Action Report',

    // Insights
    key_insight: 'Synthesized Key Insight',
    template_synthesized: 'Template Synthesized',
    data_quality_title: 'Data Provenance & Verification Note',

    // Scenario
    scenario_title: 'Monsoon Sensitivity Analysis',
    scenario_simulator: 'SCENARIO SIMULATOR',
    scenario_subtext: 'Test settlement hydrological vulnerability under varied rainfall stress. Illustrative scenario projection, not a meteorological forecast.',
    rainfall_fraction: 'Monsoon Rainfall Fraction:',
    summer_deficit: 'Summer Deficit Balance',
    baseline_rain: 'Baseline Catchment Rain',
    simulated_total: 'Simulated Total',
    chart_title: 'Simulated Monthly Runoff & Retention (mm)',

    // Evidence
    telemetry_title: 'Groundwater & Climatology Baselines',
    obs_telemetry: 'OBSERVATIONAL TELEMETRY',
    cgwb_wells: 'CGWB Monitoring Wells',
    pre_monsoon: 'Pre-Monsoon Mean Depth',
    summer_temp: 'Summer Mean Max Temp',
    monsoon_rain: 'Monsoon Precipitation',
    provenance_table_title: 'Data Source Provenance Table',
    limitations_title: 'Methodological Limitations',

    // Field Data
    field_title: 'Participatory Field Observations',
    field_subtext: 'Ground-truthing spring flow and water table measurements submitted by local field surveyors and communities.',
    log_observation: 'Log New Observation',
    obs_type: 'Observation Type',
    obs_value: 'Measurement Value',
    obs_unit: 'Unit',
    obs_notes: 'Field Notes & Landmark',
    observer_name: 'Observer Name / Gram Panchayat',
    photo_upload: 'Optional Field Photo Geotag',
    submit_obs: 'Submit Verified Observation',
    recent_obs: 'Recent Ground Observations',
    leaderboard_title: 'Community Contribution Leaderboard',

    // First Run Guide
    guide_title: 'Bhujal 3-Step Decision Guide',
    guide_step1_title: '1. Check the Safety Verdict',
    guide_step1_desc: 'Every settlement is evaluated against deterministic slope stability, landslide, and environmental rules. REJECTED sites (red hatched ring) prohibit construction.',
    guide_step2_title: '2. Understand Drivers & Scenario',
    guide_step2_desc: 'Explore the "Why?" driver decomposition for Recharge, Heat, and Spring drying. Use the Scenario tab to simulate monsoon rainfall stress.',
    guide_step3_title: '3. Sanction MGNREGA Works & DPR',
    guide_step3_desc: 'Review the Plan tab for state-calibrated wage rates and click "Generate DPR" to download the official technical dossier ZIP.',
    got_it: 'Got it, Open Map',
    next: 'Next',
    prev: 'Back',
  },

  hi: {
    brand_subtitle: 'ताप एवं जल संवेदनशीलता हेतु एआई',
    demo_badge: 'डेमो डेटा',
    search_placeholder: 'बस्ती या जिला खोजें...',
    all_states: 'सभी राज्य',
    nav_map: 'मानचित्र',
    nav_field_data: 'फ़ील्ड डेटा',
    nav_reports: 'रिपोर्ट',
    nav_about: 'डेटा एवं विवरण',
    nav_help: 'मार्गदर्शिका',

    // Safety
    verdict_safe: 'निर्माण हेतु स्वीकृत: सुरक्षित',
    verdict_conditional: 'सशर्त सुरक्षा निर्णय',
    verdict_rejected: 'अस्वीकृत — निर्माण वर्जित',
    safety_kicker: 'नियम-आधारित सुरक्षा निर्णय',
    safety_rule_label: 'लागू सुरक्षा नियम आईडी:',

    // Tabs
    tab_overview: 'अवलोकन',
    tab_agents: 'एआई एजेंट',
    tab_plan: 'कार्य योजना',
    tab_scenario: 'परिदृश्य',
    tab_evidence: 'साक्ष्य',
    agent_briefing_title: 'मल्टी-एजेंट डोमेन विशेषज्ञ परामर्श',
    agent_consult_title: 'मुख्य योजनाकार एजेंट से लाइव संवाद',
    ask_agent_placeholder: 'इस स्थल के बारे में मुख्य योजनाकार एजेंट से पूछें (उदा. क्या चेक डैम बना सकते हैं?)...',
    agent_consult_btn: 'परामर्श लें',


    // Scores
    score_recharge: 'भूजल पुनर्भरण क्षमता',
    score_heat: 'ताप एवं जल संवेदनशीलता',
    score_spring: 'झरना सूखने का जोखिम',
    why_drivers: "प्रमुख कारक ('कारण' विश्लेषण)",
    all_drivers: 'सभी कारक',
    top_drivers: 'शीर्ष 3 कारक',

    // Recommendations
    rec_title: 'अनुशंसित कार्य',
    view_plan: 'विस्तृत कार्य योजना देखें',
    generate_dpr: 'डीपीआर पैकेज डाउनलोड करें (.ZIP)',
    open_report: 'कार्य रिपोर्ट खोलें',

    // Insights
    key_insight: 'संश्लेषित मुख्य निष्कर्ष',
    template_synthesized: 'टेम्पलेट संश्लेषित',
    data_quality_title: 'डेटा स्रोत एवं सत्यापन नोट',

    // Scenario
    scenario_title: 'मानसून संवेदनशीलता विश्लेषण',
    scenario_simulator: 'परिदृश्य सिम्युलेटर',
    scenario_subtext: 'वर्षा में बदलाव के प्रभाव का परीक्षण करें। यह एक संवेदनशीलता परिदृश्य है, मौसम का पूर्वानुमान नहीं।',
    rainfall_fraction: 'मानसून वर्षा अनुपात:',
    summer_deficit: 'ग्रीष्मकालीन जल घाटा संतुलन',
    baseline_rain: 'आधारभूत जलग्रहण वर्षा',
    simulated_total: 'सिम्युलेटेड कुल वर्षा',
    chart_title: 'मासिक अपवाह एवं जल संचयन (मिमी)',

    // Evidence
    telemetry_title: 'भूजल एवं जलवायु आधारभूत आंकड़े',
    obs_telemetry: 'अवलोकनात्मक टेलीमेट्री',
    cgwb_wells: 'सीजीडब्ल्यूबी निगरानी कुएं',
    pre_monsoon: 'मानसून पूर्व औसत गहराई',
    summer_temp: 'ग्रीष्मकालीन अधिकतम तापमान',
    monsoon_rain: 'मानसून कुल वर्षा',
    provenance_table_title: 'डेटा स्रोत विवरण तालिका',
    limitations_title: 'पद्धति संबंधी सीमाएं',

    // Field Data
    field_title: 'सामुदायिक फ़ील्ड अवलोकन',
    field_subtext: 'स्थानीय ग्राम पंचायत और सर्वेक्षकों द्वारा दर्ज किए गए झरने के बहाव और जल स्तर के आंकड़े।',
    log_observation: 'नया अवलोकन दर्ज करें',
    obs_type: 'अवलोकन प्रकार',
    obs_value: 'माप मान',
    obs_unit: 'इकाई',
    obs_notes: 'फ़ील्ड टिप्पणी एवं पहचान चिह्न',
    observer_name: 'अवलोकनकर्ता / ग्राम पंचायत',
    photo_upload: 'फ़ील्ड फोटो अपलोड (वैकल्पिक)',
    submit_obs: 'अवलोकन जमा करें',
    recent_obs: 'हाल के मैदानी अवलोकन',
    leaderboard_title: 'सामुदायिक योगदानकर्ता लीडरबोर्ड',

    // First Run Guide
    guide_title: 'भूजल 3-चरणीय निर्णय मार्गदर्शिका',
    guide_step1_title: '1. सुरक्षा निर्णय की जांच करें',
    guide_step1_desc: 'प्रत्येक स्थल का ढलान और पर्यावरण नियमों के अनुसार मूल्यांकन किया जाता है। अस्वीकृत (लाल रिंग) स्थलों पर निर्माण पूर्णतः प्रतिबंधित है।',
    guide_step2_title: '2. कारक और परिदृश्य समझें',
    guide_step2_desc: 'पुनर्भरण और ताप संवेदनशीलता के प्रमुख कारणों को देखें। वर्षा के उतार-चढ़ाव का परीक्षण करने के लिए परिदृश्य टैब का उपयोग करें।',
    guide_step3_title: '3. मनरेगा कार्य और डीपीआर प्राप्त करें',
    guide_step3_desc: 'राज्य-विशिष्ट मजदूरी दरों के आधार पर लागत देखें और आधिकारिक तकनीकी डीपीआर (.ZIP) डाउनलोड करें।',
    got_it: 'समझ गए, मानचित्र खोलें',
    next: 'आगे',
    prev: 'पीछे',
  },
};
