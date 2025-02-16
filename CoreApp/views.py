from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
import os
from dotenv import load_dotenv
from openai import OpenAI
from django.http import StreamingHttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer,RegisterSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import CustomUser
from .throttles import SubscriptionThrottle
from rest_framework.throttling import ScopedRateThrottle,UserRateThrottle


# Load API keys from .env file
load_dotenv()


class GhostType(APIView):
    throttle_classes = [ UserRateThrottle  ]
    throttle_scope='user'
    authentication_classes = [JWTAuthentication]
    #permission_classes = [IsAuthenticated]
    


    def post(self, request):
        print(f"User: {request.user}")  # Debugging user
        print(f"User ID: {request.user.id}")  # Debugging user ID
        
        # Check if throttle is working
        throttle = UserRateThrottle()
        print(f"Throttle rate: {throttle.get_rate()}") 
        # Extract input from request
        user_input = request.data.get("text")
        mode = request.data.get("mode")

        # Validate input
        if not user_input:
            return Response({"error": "Missing required field: 'text'"}, status=status.HTTP_400_BAD_REQUEST)
        if mode not in [1, 2, 3, 4, 5]:
            return Response({"error": "Invalid 'mode' value. Must be between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        # Load API keys
        QWEN_API_KEY = os.getenv("QWENAPI_KEY")
        DEEPSEEK_API_KEY = os.getenv("API_KEY")
        BASE_URL = os.getenv("BASE_URL")

        # Helper function to validate AI response
        def is_invalid_response(response_text, user_input):
            response_text = response_text.strip()
            if len(response_text) > len(user_input) * 2:
                return True
            return False

        # Default: Use Qwen model
        model_name = "qwen/qwen-vl-plus:free"
        api_key = QWEN_API_KEY
        messages = []

        # Set prompt based on mode
        if mode == 1:
            messages = [
                {"role": "system", "content": "Rewrite the given text using appropriate grammar but with the same tone and return only the transformed version."},
                {"role": "user", "content": f"Only strictly rewrite the text converted into a grammatically correct sentence with the same tone and no explanation. Text: \"{user_input}\""}
            ]
        elif mode == 2:
            messages = [
                {"role": "system", "content": "Rewrite the given text in Gen Z style with the same tone and return only the transformed version."},
                {"role": "user", "content": f"Only strictly rewrite the text converted into Gen Z style with the same tone, using slang, abbreviations, and casual phrasing, but still readable. No explanation. Text: \"{user_input}\""}
            ]
        elif mode == 3:
            messages = [
                {"role": "system", "content": "Rewrite the given text in a formal tone and return only the transformed version."},
                {"role": "user", "content": f"Only strictly rewrite the text converted into a formal tone and no explanation. Text: \"{user_input}\""}
            ]
        elif mode == 4:
            messages = [
                {"role": "system", "content": "Rewrite the given text in an informal tone and return only the transformed version."},
                {"role": "user", "content": f"Only strictly return the text rewritten in an informal and conversational tone, making it relaxed and natural. No explanation. Text: \"{user_input}\""}
            ]
        elif mode == 5:
            language = request.data.get("language")
            if not language:
                return Response({"error": "Missing required field: 'language'"}, status=status.HTTP_400_BAD_REQUEST)

            messages = [
                {"role": "system", "content":"You are a translation AI. Strictly return only the translated text without any explanations or additional content ,Don't tell me how you did it just give me the text and nothing more."},
                {"role": "user", "content": f"Text : \"{user_input}\" Translate the following sentence to \"{language}\" , NO EXPLANATION NEEDED!."}
            ]

            # Switch to DeepSeek model for translations
            model_name = "deepseek/deepseek-r1-distill-llama-70b:free"
            api_key = DEEPSEEK_API_KEY

        # Log model usage
        print(f"Using model: {model_name} with API key: {api_key[:5]}*****")

        # Create OpenAI client
        client = OpenAI(api_key=api_key, base_url=BASE_URL)

        # Make the OpenAI API call
        try:
            response = client.chat.completions.create(model=model_name, messages=messages, stream=True)

            def event_stream():
                collected_response = ""  # To validate response length
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        chunk_text = chunk.choices[0].delta.content
                        collected_response += chunk_text  # Collect full response
                        yield chunk_text  # Stream each chunk as it's received
                
                # Validate AI response after complete generation
                if is_invalid_response(collected_response, user_input):
                    yield "[ERROR] AI misinterpreted the request. Please try again."

                if not collected_response.strip():
                    yield "[ERROR] AI returned an empty response."

            return StreamingHttpResponse(event_stream(), content_type="text/plain")

        except Exception as e:
            return Response({"error": f"[ERROR] API request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Custom JWT Login View
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# User Registration View
class RegisterView(generics.CreateAPIView):
    queryset=CustomUser.objects.all()
    serializer_class=RegisterSerializer
    permission_classes=[AllowAny]
