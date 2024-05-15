package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/fatih/color"
	"github.com/jedib0t/go-pretty/v6/table"
	"github.com/jedib0t/go-pretty/v6/text"
	"github.com/olekukonko/tablewriter"
)

type CommentRules struct {
	singleLine     string
	multiLineStart string
	multiLineEnd   string
}

type CommentRulesRegistry struct {
	rules map[string]CommentRules
}

func (r *CommentRulesRegistry) register(language, singleLine, multiLineStart, multiLineEnd string) {
	r.rules[language] = CommentRules{
		singleLine:     singleLine,
		multiLineStart: multiLineStart,
		multiLineEnd:   multiLineEnd,
	}
}

func (r *CommentRulesRegistry) getRules(language string) (CommentRules, bool) {
	rule, exists := r.rules[language]
	return rule, exists
}

type CounterCodeInfo struct {
	languageStats map[string][3]int
	files         []string
	readFiles     []string
	nonReadFiles  []string
	registry      *CommentRulesRegistry
}

func NewCounterCodeInfo(files []string, registry *CommentRulesRegistry) *CounterCodeInfo {
	return &CounterCodeInfo{
		languageStats: make(map[string][3]int),
		files:         files,
		registry:      registry,
	}
}

func (c *CounterCodeInfo) run() {
	for _, filename := range c.files {
		if _, err := os.Stat(filename); os.IsNotExist(err) {
			c.nonReadFiles = append(c.nonReadFiles, filename)
			fmt.Printf("Error processing file %s: not exist\n", filename)
		} else {
			if fileInfo, _ := os.Stat(filename); fileInfo.IsDir() {
				c.processDirectory(filename)
			} else {
				c.processFile(filename)
			}
		}
	}
}

func (c *CounterCodeInfo) detectLanguage(filename string) (string, bool) {
	extensionMap := map[string]string{
		"py":   "python",
		"js":   "javascript",
		"go":   "go",
		"cpp":  "cpp",
		"h":    "cpp",
		"mod":  "go",
		"java": "java",
	}

	ext := strings.TrimPrefix(filepath.Ext(filename), ".")
	language, exists := extensionMap[ext]
	if exists {
		c.readFiles = append(c.readFiles, filename)
		return language, true
	}
	c.nonReadFiles = append(c.nonReadFiles, filename)
	return "", false
}

func (c *CounterCodeInfo) countLines(filename, language string) (int, int, int) {
	rules, exists := c.registry.getRules(language)
	if !exists {
		fmt.Printf("No rules registered for language: %s\n", language)
		return 0, 0, 0
	}

	totalLines := 0
	commentLines := 0
	blankLines := 0
	inBlockComment := false

	file, err := os.Open(filename)
	if err != nil {
		fmt.Printf("Error opening file %s: %v\n", filename, err)
		return 0, 0, 0
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		totalLines++

		if line == "" {
			blankLines++
			continue
		}

		if inBlockComment {
			commentLines++
			if strings.Contains(line, rules.multiLineEnd) {
				inBlockComment = false
			}
			continue
		}

		if strings.HasPrefix(line, rules.singleLine) {
			commentLines++
		} else if strings.Contains(line, rules.multiLineStart) {
			commentLines++
			inBlockComment = true
			if strings.Contains(line, rules.multiLineEnd) {
				inBlockComment = false
			}
		}
	}

	return totalLines, commentLines, blankLines
}

func (c *CounterCodeInfo) processDirectory(directory string) {
	filepath.Walk(directory, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			language, exists := c.detectLanguage(path)
			if exists {
				lines, commentLines, blankLines := c.countLines(path, language)
				stats := c.languageStats[language]
				stats[0] += lines
				stats[1] += commentLines
				stats[2] += blankLines
				c.languageStats[language] = stats
			}
		}
		return nil
	})
}

func (c *CounterCodeInfo) processFile(filename string) {
	language, exists := c.detectLanguage(filename)
	if exists {
		totalLines, commentLines, blankLines := c.countLines(filename, language)
		stats := c.languageStats[language]
		stats[0] += totalLines
		stats[1] += commentLines
		stats[2] += blankLines
		c.languageStats[language] = stats
	}
}
func (c *CounterCodeInfo) show() {
	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	t.SetStyle(table.StyleLight)

	// Set header with colored text for each column
	t.AppendHeader(table.Row{
		text.FgBlue.Sprintf("Language"),
		text.FgGreen.Sprintf("Total lines"),
		text.FgYellow.Sprintf("Comment lines"),
		text.FgMagenta.Sprintf("Blank lines"),
	})

	for language, stats := range c.languageStats {
		// Append row with colored text for each column
		t.AppendRow(table.Row{
			text.FgBlue.Sprintf("%v", language),
			text.FgGreen.Sprintf("%v", stats[0]),
			text.FgYellow.Sprintf("%v", stats[1]),
			text.FgMagenta.Sprintf("%v", stats[2]),
		})
	}

	// Calculate total counts
	totalLines := 0
	totalCommentLines := 0
	totalBlankLines := 0
	for _, stats := range c.languageStats {
		totalLines += stats[0]
		totalCommentLines += stats[1]
		totalBlankLines += stats[2]
	}

	// Add a blank row before the footer
	t.AppendRow(table.Row{})

	// Add footer with total counts
	t.AppendFooter(table.Row{
		text.FgRed.Sprintf("Total"),
		text.FgGreen.Sprintf("%v", totalLines),
		text.FgYellow.Sprintf("%v", totalCommentLines),
		text.FgMagenta.Sprintf("%v", totalBlankLines),
	})

	// Render the table
	t.Render()
}

func (c *CounterCodeInfo) show2() {
	fmt.Printf("Files source: %v\n", c.files)
	fmt.Printf("Total files: %d\n", len(c.readFiles)+len(c.nonReadFiles))
	fmt.Printf("Processed files: %d\n", len(c.readFiles))
	fmt.Printf("Skipped files: %d\n", len(c.nonReadFiles))

	totalLines := 0
	totalCommentLines := 0
	totalBlankLines := 0

	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"Language", "Total lines", "Comment lines", "Blank lines"})
	table.SetBorder(true)         // Set border to true
	table.SetCenterSeparator("|") // Set column separator

	for language, stats := range c.languageStats {
		table.Append([]string{
			color.CyanString(language),
			color.GreenString(fmt.Sprintf("%d", stats[0])),
			color.YellowString(fmt.Sprintf("%d", stats[1])),
			color.MagentaString(fmt.Sprintf("%d", stats[2])),
		})
		totalLines += stats[0]
		totalCommentLines += stats[1]
		totalBlankLines += stats[2]
	}

	// Add footer with total counts
	table.Append([]string{
		color.RedString("Total"),
		color.GreenString(fmt.Sprintf("%d", totalLines)),
		color.YellowString(fmt.Sprintf("%d", totalCommentLines)),
		color.MagentaString(fmt.Sprintf("%d", totalBlankLines)),
	})

	table.Render()
}

func (c *CounterCodeInfo) show1() {
	fmt.Printf("Files source: %v\n", c.files)
	fmt.Printf("Total files: %d\n", len(c.readFiles)+len(c.nonReadFiles))
	fmt.Printf("Processed files: %d\n", len(c.readFiles))
	fmt.Printf("Skipped files: %d\n", len(c.nonReadFiles))

	totalLines := 0
	totalCommentLines := 0
	totalBlankLines := 0

	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	t.SetStyle(table.StyleColoredBright)
	t.AppendHeader(table.Row{
		color.CyanString("Language"),
		color.GreenString("Total lines"),
		color.YellowString("Comment lines"),
		color.MagentaString("Blank lines"),
	})

	for language, stats := range c.languageStats {
		t.AppendRow(table.Row{
			color.CyanString(language),
			color.GreenString(fmt.Sprintf("%d", stats[0])),
			color.YellowString(fmt.Sprintf("%d", stats[1])),
			color.MagentaString(fmt.Sprintf("%d", stats[2])),
		})
		totalLines += stats[0]
		totalCommentLines += stats[1]
		totalBlankLines += stats[2]
	}

	t.AppendFooter(table.Row{
		color.RedString("Total"),
		color.GreenString(fmt.Sprintf("%d", totalLines)),
		color.YellowString(fmt.Sprintf("%d", totalCommentLines)),
		color.MagentaString(fmt.Sprintf("%d", totalBlankLines)),
	})

	t.Render()
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run main.go <filename_or_directory>")
		return
	}

	registry := &CommentRulesRegistry{rules: make(map[string]CommentRules)}
	registry.register("python", "#", "\"\"\"", "\"\"\"")
	registry.register("javascript", "//", "/*", "*/")
	registry.register("go", "//", "/*", "*/")
	registry.register("cpp", "//", "/*", "*/")
	registry.register("java", "//", "/*", "*/")

	path := os.Args[1:]
	cci := NewCounterCodeInfo(path, registry)
	cci.run()
	cci.show()
	cci.show1()
	cci.show2()
}
