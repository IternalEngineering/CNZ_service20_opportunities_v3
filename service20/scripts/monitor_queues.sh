#!/bin/bash
# Linux/Mac shell script to monitor SQS queues

echo "============================================================"
echo "SQS Queue Monitor for Service20"
echo "============================================================"
echo ""

show_menu() {
    echo "Select monitoring mode:"
    echo "  1. Monitor once"
    echo "  2. Monitor continuously (5 second refresh)"
    echo "  3. Monitor continuously (30 second refresh)"
    echo "  4. Health check only"
    echo "  5. JSON output"
    echo "  6. Exit"
    echo ""
}

while true; do
    show_menu
    read -p "Enter choice (1-6): " choice

    case $choice in
        1)
            python3 monitor_queues.py --mode once
            break
            ;;
        2)
            python3 monitor_queues.py --mode continuous --interval 5
            break
            ;;
        3)
            python3 monitor_queues.py --mode continuous --interval 30
            break
            ;;
        4)
            python3 monitor_queues.py --mode health
            break
            ;;
        5)
            python3 monitor_queues.py --mode json
            break
            ;;
        6)
            echo "Goodbye!"
            break
            ;;
        *)
            echo "Invalid choice!"
            echo ""
            ;;
    esac
done
