/**
 * Bible QA JavaScript functionality
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const qaForm = document.getElementById('qaForm');
    const questionInput = document.getElementById('question');
    const contextInput = document.getElementById('context');
    const loader = document.getElementById('loader');
    const resultDiv = document.getElementById('result');
    const answerParagraph = document.getElementById('answer');
    const modelInfoParagraph = document.getElementById('model-info');
    
    // Sample questions for inspiration
    const sampleQuestions = [
        "What does Genesis 1:1 say?",
        "How does the Bible describe faith in Hebrews 11:1?",
        "What does John 3:16 mean?",
        "Who was King David in the Bible?",
        "What is the significance of the Sermon on the Mount?",
        "How many books are in the Bible?"
    ];
    
    // Set a random sample question as placeholder
    questionInput.placeholder = sampleQuestions[Math.floor(Math.random() * sampleQuestions.length)];
    
    // Handle form submission
    qaForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        const context = contextInput.value.trim();
        
        if (!question) {
            showError("Please enter a question");
            return;
        }
        
        // Show loading indicator
        loader.style.display = 'block';
        resultDiv.style.display = 'none';
        
        try {
            const response = await fetch('/api/question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    context: context
                }),
            });
            
            const data = await response.json();
            
            // Hide loader
            loader.style.display = 'none';
            
            // Process response
            if (response.ok && data.status === 'success') {
                showResult(data.answer, data.model_info);
            } else {
                showError(data.message || "Failed to get an answer. Please try again.");
            }
        } catch (error) {
            loader.style.display = 'none';
            showError(error.message || "An error occurred. Please try again.");
        }
    });
    
    // Function to display the result
    function showResult(answer, modelInfo) {
        answerParagraph.textContent = answer;
        modelInfoParagraph.textContent = `Model: ${modelInfo.model_type || 'Bible QA'}`;
        resultDiv.style.display = 'block';
    }
    
    // Function to display an error
    function showError(message) {
        answerParagraph.textContent = `Error: ${message}`;
        modelInfoParagraph.textContent = '';
        resultDiv.style.display = 'block';
    }
}); 