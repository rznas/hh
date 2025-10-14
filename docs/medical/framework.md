# AI Ocular Triage Framework

> **Source**: Original framework document  
> **Last Updated**: 2025-01-15  
> **Status**: Primary Reference  
> **For Claude Code**: This is the authoritative source for triage logic

**Framework for the AI Ocular Triage Agent**

This framework is designed to be methodical, safe, and legally defensible.

**Phase 1: Pre-Interaction & Consent**

* **Critical Disclaimer:** Before any questions begin, the user must acknowledge a clear, unambiguous disclaimer:

  * "I am an AI assistant, not a medical doctor. I am designed for informational and triage purposes only. This is not a substitute for professional medical diagnosis or treatment. In case of a true medical emergency (e.g., sudden vision loss, severe trauma, chemical burn), please disconnect and call Emergency Services immediately."

  * User must click "I Understand" to proceed.

* **Data Privacy Policy:** Briefly state how their data will be used and stored, with a link to the full policy.

**Phase 2: Patient Intake & Chief Complaint**

* **Ask:** Age, Gender (with "Prefer not to say" option).

* **Chief Complaint:** Open-ended question: "Please describe your eye problem in your own words."

* **AI Clarification & Standardization:**

  * The AI uses NLP to parse the free-text input.

  * It identifies key terms and asks 1-3 targeted, multiple-choice or yes/no questions to clarify and standardize the complaint (e.g., User says "eye red," AI asks: "Is the redness in one eye or both?" "Is there any pain?" "Is there any discharge?").

  * This step generates a **standardized chief complaint** (e.g., "Unilateral Red Eye with Purulent Discharge").

**Phase 3: Directed Triage & Risk Stratification (The Core Algorithm)**  
This is a rule-based system powered by your GraphRAG, which acts as the knowledge source for the rules.

1. **Immediate "Red Flag" Triage:** The AI first checks the chief complaint and initial data against a pre-defined list of **"High-Risk Triggers"** that mandate immediate referral. This bypasses all other questioning for safety.

   * **Triggers:** Sudden, painless vision loss; severe ocular trauma; chemical splash; seeing new floaters with flashes of light; sudden double vision; penetrating injury.

   * **Action:** If triggered, the AI immediately states: "Based on your description, this requires immediate medical attention. Please go to the nearest emergency room or call for an ambulance. I have located the nearest emergency departments for you: \[List/Map\]. Would you like me to call someone?"

2. **Systematic Symptom Interrogation:** If no immediate red flags are present, the AI begins a structured interview.

   * The GraphRAG is queried with the standardized chief complaint to retrieve a list of potential diagnoses (DDx), each tagged with **urgency level (Emergent, Urgent, Non-Urgent)** and associated symptoms, history, and "virtual tests."

   * **The AI does NOT think in probabilities first.** It follows a **Safety-First Decision Tree**:

     * **Step A: Rule Out Emergent Conditions.** It will ask about the key symptoms and history for all *Emergent* conditions on the DDx list.

     * **"Triage Threshold":** Your 0.2 (20%) suspicion is a good concept. If the likelihood of *any* emergent condition crosses this threshold based on the answers, the process stops, and the user is referred to the ER/Urgent Care.

     * **Step B: Rule Out Urgent Conditions.** Only if all emergent conditions are ruled out (likelihood \<0.2), it moves to *Urgent* conditions.

     * **Step C: Identify Non-Urgent Conditions.** Only after ruling out urgent issues, it narrows down to *Non-Urgent* conditions.

3. **"Virtual Exam":** The AI can instruct the user to perform simple, safe self-tests.

   * *Examples:* "Cover one eye at a time and tell me if your vision is blurry in one." "Can you move your eye in all directions without pain?" "Gently press on the lower eyelid—does it cause pain?"

   * **Crucially, it will NOT ask users to touch their eye if there is pain or suspicion of injury/infection.**

**Phase 4: Summary & Action Plan**

* **Triage Outcome:** The AI clearly states its conclusion: "My assessment suggests this is likely a \[e.g., Non-Emergent condition like Allergic Conjunctivitis\]. However, an in-person examination is required for a definitive diagnosis."

* **Educational Component:** Provides a brief, plain-language explanation from the GraphRAG source (e.g., "Bacterial Conjunctivitis is an infection caused by bacteria...").

* **Home Care Advice:** Suggests safe, supportive measures (e.g., "Use artificial tears," "Apply a cool compress," "Avoid wearing contact lenses."). **Explicitly avoids recommending specific OTC drugs without a doctor's prescription.**

* **Definitive Call to Action:**

  * **Non-Urgent:** "I recommend scheduling an appointment with an ophthalmologist within the next 1-2 weeks."

  * **Urgent:** "You should see a doctor within 24-48 hours. I can help you find an urgent care clinic or an ophthalmologist with same-day availability."

  * **Seamless Integration:** "I can show you available appointments from highly-rated ophthalmologists near you." \-\> Integrates with [Paziresh24.ir](https://paziresh24.ir/), nobat.ir, etc., showing available slots.

**Phase 5: Post-Interaction**

* Provide a summary report that the user can save or email to themselves to show their doctor.

* Option to set a reminder for their appointment.

