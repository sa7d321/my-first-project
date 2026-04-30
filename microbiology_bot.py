"""
Microbiology Study Bot - Helps students find study materials, exams, and lab photos
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_SUBJECT, CHOOSING_RESOURCE = range(2)

# Study materials database - customize with your content
SUBJECTS = {
    'Bacterial Cell': {
        'study_materials': 'Link to Bacterial Cell structure notes: https://example.com/bacterial_cell',
        'exam_content': 'Topics: Cell wall, membrane, ribosomes, flagella',
        'lab_photos': 'Lab photos available at: https://example.com/bacterial_photos'
    },
    'Fermentation': {
        'study_materials': 'Link to Fermentation processes: https://example.com/fermentation',
        'exam_content': 'Topics: Aerobic respiration, anaerobic respiration, ATP production',
        'lab_photos': 'Lab photos available at: https://example.com/fermentation_photos'
    },
    'Virology': {
        'study_materials': 'Link to Viral structures: https://example.com/virology',
        'exam_content': 'Topics: Viral classification, replication cycle, pathogenesis',
        'lab_photos': 'Lab photos available at: https://example.com/viral_photos'
    },
    'Immunology': {
        'study_materials': 'Link to Immune system: https://example.com/immunology',
        'exam_content': 'Topics: Antibodies, antigens, immune response, vaccination',
        'lab_photos': 'Lab photos available at: https://example.com/immune_photos'
    },
    'Microbial Genetics': {
        'study_materials': 'Link to Genetic principles: https://example.com/genetics',
        'exam_content': 'Topics: DNA, mutation, conjugation, transformation',
        'lab_photos': 'Lab photos available at: https://example.com/genetics_photos'
    },
}

RESOURCE_TYPES = ['study_materials', 'exam_content', 'lab_photos']


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the bot and display subject options."""
    reply_keyboard = [[subject] for subject in SUBJECTS.keys()]
    reply_keyboard.append(['Cancel'])
    
    await update.message.reply_text(
        '🔬 Welcome to Microbiology Study Bot! 🔬\n\n'
        'Select a subject to find study materials, exam content, or lab photos:\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Choose a subject..."
        ),
    )
    return CHOOSING_SUBJECT


async def select_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subject selection."""
    subject = update.message.text
    
    if subject == 'Cancel':
        await update.message.reply_text(
            'Goodbye! Feel free to return anytime to study.',
            reply_markup=ReplyKeyboardRemove(),
        )
        return -1
    
    if subject not in SUBJECTS:
        await update.message.reply_text(
            f'Sorry, "{subject}" is not available. Please select from the list.'
        )
        return CHOOSING_SUBJECT
    
    context.user_data['selected_subject'] = subject
    
    reply_keyboard = [
        ['📚 Study Materials'],
        ['📝 Exam Content'],
        ['🔬 Lab Photos'],
        ['🔙 Back'],
    ]
    
    await update.message.reply_text(
        f'You selected: <b>{subject}</b>\n\n'
        'What would you like to access?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Choose resource type..."
        ),
        parse_mode='HTML',
    )
    return CHOOSING_RESOURCE


async def select_resource(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle resource type selection and send information."""
    user_choice = update.message.text
    subject = context.user_data.get('selected_subject')
    
    if user_choice == '🔙 Back':
        return await start(update, context)
    
    # Map emoji choices to resource keys
    choice_map = {
        '📚 Study Materials': 'study_materials',
        '📝 Exam Content': 'exam_content',
        '🔬 Lab Photos': 'lab_photos',
    }
    
    resource_key = choice_map.get(user_choice)
    
    if resource_key and subject in SUBJECTS:
        resource_content = SUBJECTS[subject][resource_key]
        
        emoji_map = {
            'study_materials': '📚',
            'exam_content': '📝',
            'lab_photos': '🔬',
        }
        emoji = emoji_map.get(resource_key, '📌')
        
        await update.message.reply_text(
            f'{emoji} <b>{subject} - {user_choice}</b>\n\n'
            f'{resource_content}',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            'Invalid selection. Please try again.'
        )
    
    # Ask if they want to continue
    reply_keyboard = [
        ['🔄 Search Another Subject'],
        ['❌ Exit'],
    ]
    
    await update.message.reply_text(
        'What would you like to do next?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
        ),
    )
    return CHOOSING_SUBJECT


async def handle_next_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's next action."""
    user_choice = update.message.text
    
    if user_choice == '🔄 Search Another Subject':
        return await start(update, context)
    elif user_choice == '❌ Exit':
        await update.message.reply_text(
            '👋 Goodbye! Good luck with your studies!',
            reply_markup=ReplyKeyboardRemove(),
        )
        return -1
    else:
        return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text(
        '❌ Operation cancelled. Type /start to begin again.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return -1


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with available commands."""
    help_text = (
        '📚 <b>Microbiology Bot - Help</b>\n\n'
        'Commands:\n'
        '/start - Start the bot and search for study materials\n'
        '/help - Show this help message\n\n'
        'Available Subjects:\n'
    )
    
    for i, subject in enumerate(SUBJECTS.keys(), 1):
        help_text += f'{i}. {subject}\n'
    
    help_text += '\nFor each subject, you can find:\n' \
                 '• Study Materials\n' \
                 '• Exam Content\n' \
                 '• Lab Photos'
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a reply."""
    logger.error(f'Update {update} caused error {context.error}')
    
    if update and update.message:
        await update.message.reply_text(
            '❌ An error occurred. Please try again or use /start to restart.'
        )


def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token from BotFather
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_SUBJECT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    select_subject
                ),
            ],
            CHOOSING_RESOURCE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    select_resource
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_next_action
            ),
        ],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot started. Polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
