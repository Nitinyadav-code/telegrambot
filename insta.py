from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import instaloader
import os
import re
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot configuration
BOT_TOKEN = "7609570776:AAGXVEu174cMm331R8RKqbGWl9UrBGbCGAM"

# Initialize Instagram loader
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

def is_valid_instagram_url(url: str) -> bool:
    pattern = r'https?://(?:www\.)?instagram\.com/(?:p|reel)/[\w-]+/?'
    return bool(re.match(pattern, url))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome! I can help you download Instagram posts and reels.\n"
        "Just send me an Instagram post/reel URL."
    )

async def handle_instagram_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    if not is_valid_instagram_url(url):
        await update.message.reply_text("❌ Please send a valid Instagram post or reel URL")
        return
        
    status_msg = await update.message.reply_text("⏳ Processing your request...")
    download_path = None
    
    try:
        path = urlparse(url).path
        shortcode = path.split('/')[-2]
        
        # Create base downloads directory
        base_path = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(base_path, exist_ok=True)
        
        # Set specific download path
        download_path = os.path.join(base_path, shortcode)
        if os.path.exists(download_path):
            import shutil
            shutil.rmtree(download_path)
        os.makedirs(download_path)

        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
        except Exception as e:
            await status_msg.edit_text(f"❌ Failed to fetch post: {str(e)}")
            return

        await status_msg.edit_text("📥 Downloading content...")
        L.dirname_pattern = download_path
        L.download_post(post, target=shortcode)

        if post.is_video:
            video_files = [f for f in os.listdir(download_path) if f.endswith('.mp4')]
            if video_files:
                await status_msg.edit_text("📤 Uploading video...")
                with open(os.path.join(download_path, video_files[0]), 'rb') as video:
                    await update.message.reply_video(
                        video=video,
                        caption="🎥 INSTAGRAM REEL DOWNLOADER\n\n"
                                "✨ Downloaded By: @{}\n"
                                "❤️ Hope you enjoy your reel!\n"
                                "✅ Downloaded successfully!".format( "❤️ Anonymous")
                    )
        else:
            image_files = [f for f in os.listdir(download_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            if image_files:
                await status_msg.edit_text("📤 Uploading images...")
                for img_file in image_files:
                    if img_file.endswith(('.jpg', '.jpeg', '.png')):
                        with open(os.path.join(download_path, img_file), 'rb') as photo:
                            await update.message.reply_photo(
                                photo=photo,
                                caption="🎥 INSTAGRAM REEL DOWNLOADER\n\n"
                                "✨ Downloaded By: @{}\n"
                                "❤️ Hope you enjoy your reel!\n"
                                "✅ Downloaded successfully!".format( "❤️ Anonymous")
                            )
        await status_msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")
    finally:
        if download_path and os.path.exists(download_path):
            import shutil
            shutil.rmtree(download_path)

def main() -> None:
    # Initialize application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'https?://(?:www\.)?instagram\.com/(?:p|reel)/[\w-]+/?'),
        handle_instagram_url
    ))

    # Start the bot
    print("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()