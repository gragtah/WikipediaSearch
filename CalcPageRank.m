%% Read in links from file and generate Page Rank for the collection.

disp('Calculating PageRank...')

input_file = 'matlabInputFile.dat';

[status, result] = system(['wc -l ' input_file ' | awk ' char(39) '{print $1}' char(39)]);
line_count = str2num(result);

adj = sparse(line_count, line_count);

fd = fopen(input_file, 'r');

curr_line = 1;
while (~feof(fd))
    links = fgetl(fd);
    % Split on spaces to get each link ID.
    if ~strcmp(links, '')
        linkIDs = cellfun(@str2num, regexp(links(1:end-1), ' ', 'split'));
        
        % Collection is 0-based, MATLAB is 1-based indexing
        linkIDs = linkIDs + 1;
        
        % Update the adjacency matrix to include the links.
        adj(curr_line, linkIDs) = 1;
    end
    curr_line = curr_line + 1;
end

fclose(fd);

matlabpool open 4

%% For all docs with at least one outgoing link, replace each 1 with 1 / row sum.

adj_sums = sum(adj, 2);
parfor row = 1:line_count
    if (adj_sums(row) > 0)
        adj(row, :) = adj(row, :) ./ adj_sums(row);
    end
end

% Account for the probability the user jumps to a random URL rather
% than clicking an outgoing link.
alpha = 0.1;
adj = (1 - alpha) .* adj;

% Calculate the column vector of how much needs to be added to account
% for the URL bar:
I = (adj_sums > 0)*(alpha/line_count) + (adj_sums == 0)*(1/line_count);

% Choose arbitrary starting point.
x = zeros(1, line_count);
x(1) = 1;

% Iterate t=128 steps.
for i= 1:128
    add_amount = x * I;
    x = x * adj + repmat(add_amount, 1, line_count);
end

matlabpool close

% Write result to file.
output = fopen('pageRank.dat', 'w');
for i = 1:line_count
    fprintf(output, '%g\n', x(i));
end
fclose(output);


